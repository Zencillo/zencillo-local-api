[CmdletBinding(SupportsShouldProcess, ConfirmImpact='Medium')]
param(
    [Parameter(Mandatory)]
    [ValidateSet('Setup','Prepare','Import','Receive','Install','Update','Uninstall','Start','Stop','Status')]
    [string]$Action,
    [string]$Bundle,
    [string]$WinSWHash,
    [string]$Station,
    [string]$Listen,
    [string]$DnsName,
    [ValidateRange(1,65535)][int]$Port = 8765,
    [string]$LanSubnet,
    [string]$Certificate,
    [string]$PrivateKey,
    [string]$DevicesFile,
    [string]$CapturadorDatabase,
    [string]$ImportSourceIp,
    [string]$ConfirmStation,
    [ValidateRange(1,65535)][int]$ImportPort = 8766,
    [switch]$ReplaceSql,
    [switch]$AcceptOdbcLicense,
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'
$service = 'ZencilloLocalApi'
$principal = "NT SERVICE\$service"
$binary = Join-Path $env:ProgramFiles $service
$data = Join-Path $env:ProgramData $service
$config = Join-Path $data 'service.json'
$logs = Join-Path $data 'logs'
$wrapper = Join-Path $binary "$service.exe"
$wrapperConfig = Join-Path $binary "$service.xml"
$python = Join-Path $binary 'runtime\python.exe'
$rule = "$service-HTTPS"
$registered = Get-Service -Name $service -ErrorAction SilentlyContinue

if ($Action -eq 'Status') {
    if (!$registered) { 'Servicio no registrado.' } else { $registered | Select-Object Name, Status, StartType }
    return
}
if (!$Apply -or !$PSCmdlet.ShouldProcess("$Service de esta estación", $Action)) {
    "Vista previa $Action. No se aplicaron cambios. Use -Apply para ejecutar."
    return
}
if (!(New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Ejecute el instalador elevado.'
}

function Invoke-Native([string]$Executable, [string[]]$Arguments) {
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Falló $([IO.Path]::GetFileName($Executable)) (código $LASTEXITCODE)." }
}

function Protect-Folder([string]$Path, [string]$ServiceAccess) {
    if ((Get-Item -LiteralPath $Path).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw 'Se rechaza una ruta de instalación redirigida.'
    }
    $acl = [Security.AccessControl.DirectorySecurity]::new()
    $acl.SetAccessRuleProtection($true,$false)
    $administrators = [Security.Principal.SecurityIdentifier]::new('S-1-5-32-544')
    $system = [Security.Principal.SecurityIdentifier]::new('S-1-5-18')
    $acl.SetOwner($administrators)
    foreach ($sid in @($administrators, $system)) {
        $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new(
            $sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow'))
    }
    if ($ServiceAccess) {
        $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new(
            $principal, $ServiceAccess,'ContainerInherit,ObjectInherit','None','Allow'))
    }
    Set-Acl -LiteralPath $Path -AclObject $acl
}

function Stage-Files([string]$Destination) {
    if (!$Bundle -or !$WinSWHash -or $WinSWHash -notmatch '^[a-fA-F0-9]{64}$') {
        throw 'Indique el paquete y el SHA-256 confiable de WinSW.'
    }
    & (Join-Path $PSScriptRoot 'Test-StationBundle.ps1') -Bundle $Bundle
    $binarySource = Join-Path $Bundle 'WinSW.exe'
    if ((Get-FileHash -LiteralPath $binarySource -Algorithm SHA256).Hash -ne $WinSWHash) {
        throw 'El hash de WinSW no coincide.'
    }
    foreach ($part in @('runtime','importer','WinSW.exe')) {
        $entry = Get-Item -LiteralPath (Join-Path $Bundle $part)
        if (($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) -or
            ($entry.PSIsContainer -and (Get-ChildItem -LiteralPath $entry.FullName -Recurse -Attributes ReparsePoint))) {
            throw 'El paquete contiene vínculos.'
        }
    }
    Copy-Item -LiteralPath (Join-Path $Bundle 'runtime') -Destination $Destination -Recurse
    Copy-Item -LiteralPath (Join-Path $Bundle 'importer') -Destination $Destination -Recurse
    Copy-Item -LiteralPath $binarySource -Destination (Join-Path $Destination "$service.exe")
}

function Write-Wrapper {
    $document = [xml]'<service><id>ZencilloLocalApi</id><name>Zencillo Local API</name><description>API local de la estación</description><executable/><arguments/><workingdirectory/><startmode>Manual</startmode><stoptimeout>20sec</stoptimeout><logpath/><log mode="roll-by-size"><sizeThreshold>10240</sizeThreshold><keepFiles>5</keepFiles></log><onfailure action="restart" delay="15 sec"/><onfailure action="restart" delay="60 sec"/><onfailure action="none"/><resetfailure>1 hour</resetfailure></service>'
    $document.service.executable = $python
    $document.service.arguments = "-I -m app.station_service --config ""$config"""
    $document.service.workingdirectory = $binary
    $document.service.logpath = $logs
    $document.Save((Join-Path $binary "$service.xml"))
}

function Test-Subnet($Address, $Cidr) {
    if ($Address -notmatch '^(\d{1,3}\.){3}\d{1,3}$' -or
        $Cidr -notmatch '^((\d{1,3}\.){3}\d{1,3})/([0-9]{1,2})$') {
        throw 'Indique IPv4 y una subred CIDR de estación.'
    }
    $network = [Net.IPAddress]::Parse($Matches[1])
    $length = [int]$Matches[3]
    $ip = [Net.IPAddress]::Parse($Address)
    $octets = $ip.GetAddressBytes()
    $minLength = if ($octets[0] -eq 10) { 8 } elseif ($octets[0] -eq 172 -and $octets[1] -ge 16 -and $octets[1] -le 31) { 12 } elseif ($octets[0] -eq 192 -and $octets[1] -eq 168) { 16 } else { 33 }
    if ($length -lt $minLength -or $length -gt 32) { throw 'La subred debe pertenecer a la LAN privada.' }
    $net = $network.GetAddressBytes()
    $remaining = $length
    for ($index = 0; $index -lt 4 -and $remaining -gt 0; $index++) {
        $bits = [Math]::Min(8,$remaining)
        $mask = 256 - [int][Math]::Pow(2,(8-$bits))
        if (($octets[$index] -band $mask) -ne ($net[$index] -band $mask)) { throw 'La IP no pertenece a la subred.' }
        $remaining -= $bits
    }
}

function Test-ApiReady($Site) {
    $uri = "https://$($Site.dnsName):$($Site.port)/healthz"
    $deadline = [DateTime]::UtcNow.AddSeconds(20)
    do {
        try {
            $response = Invoke-WebRequest -Uri $uri -UseBasicParsing -MaximumRedirection 0 -TimeoutSec 3
            if ($response.StatusCode -eq 200 -and ($response.Content | ConvertFrom-Json).status -eq 'ok') { return }
        } catch { }
        Start-Sleep -Milliseconds 500
    } while ([DateTime]::UtcNow -lt $deadline)
    throw 'La API no respondió con HTTPS verificable. Revise DNS, certificado, firewall y servicio.'
}

function Import-Capturador {
    $importer = Join-Path $binary 'importer\CapturadorWindows.exe'
    if (Get-Process -Name 'CapturadorWindows' -ErrorAction SilentlyContinue) {
        throw 'Cierre Capturador antes de abrir su configuración local.'
    }
    if (!$CapturadorDatabase) { throw 'Indique la carpeta db de la instalación Capturador.' }
    $directory = (Resolve-Path -LiteralPath $CapturadorDatabase).Path
    $arguments = '"{0}" "{1}" "{2}"' -f $directory.TrimEnd('\'),$python,$data
    if ($ReplaceSql) { $arguments += ' --replace' }
    $importProcess = Start-Process -FilePath $importer -WorkingDirectory (Split-Path -Parent $importer) -ArgumentList $arguments -Wait -PassThru
    if ($importProcess.ExitCode -ne 0) { throw 'No se confirmó el perfil SQL. Revise que Capturador esté cerrado y que el usuario, la base y el certificado SQL sean válidos.' }
}

switch ($Action) {
    'Setup' {
        if (!$CapturadorDatabase) { throw 'Indique la carpeta db del Capturador Windows.' }
        if (!$Bundle) { $Bundle = $PSScriptRoot }
        if (!$WinSWHash) {
            $WinSWHash = (Get-Content -LiteralPath (Join-Path $Bundle 'WinSW.sha256') -Raw).Trim()
        }
        if ($registered) { throw 'La estación ya tiene un servicio Local API. Use Verificar o el procedimiento de actualización.' }
        if (Test-Path -LiteralPath $config) {
            $saved = Get-Content -LiteralPath $config -Raw | ConvertFrom-Json
            $targetName = if ($DnsName) { $DnsName } else { $Listen }
            if ($saved.station -ne $Station -or $saved.listen -ne $Listen -or
                $saved.dnsName -ne $targetName -or $saved.port -ne $Port -or $saved.subnet -ne $LanSubnet) {
                throw 'El perfil preparado corresponde a otra estación o dirección. Revise la configuración antes de continuar.'
            }
            if (Test-Path -LiteralPath (Join-Path $data 'sql.dpapi') -PathType Leaf) {
                if (!$ReplaceSql) { $CapturadorDatabase = '' }
            }
        } else {
            & $PSCommandPath -Action Prepare -Bundle $Bundle -WinSWHash $WinSWHash -Station $Station -Listen $Listen `
                -DnsName $DnsName -Port $Port -LanSubnet $LanSubnet -Certificate $Certificate `
                -PrivateKey $PrivateKey -DevicesFile $DevicesFile -AcceptOdbcLicense:$AcceptOdbcLicense -Apply -Confirm:$false
        }
        & $PSCommandPath -Action Install -CapturadorDatabase $CapturadorDatabase -ReplaceSql:$ReplaceSql -Apply -Confirm:$false
    }
    'Import' { Import-Capturador }
    'Receive' {
        if ($ConfirmStation -notmatch '^[1-9][0-9]*/[1-9][0-9]*/[1-9][0-9]*$') {
            throw 'Confirme compañía/centro/isla del Capturador autorizado.'
        }
        $site = Get-Content -LiteralPath $config -Raw | ConvertFrom-Json
        Test-Subnet $ImportSourceIp $site.subnet
        if ($ImportPort -eq $site.port) { throw 'El puerto temporal debe ser distinto del operativo.' }
        $temporaryRule = "$service-Import-$([Guid]::NewGuid().ToString('N'))"
        New-NetFirewallRule -Name $temporaryRule -DisplayName 'Zencillo Local API (importación temporal)' -Direction Inbound -Action Allow -Protocol TCP -LocalAddress $site.listen -LocalPort $ImportPort -RemoteAddress $ImportSourceIp -Profile Domain,Private | Out-Null
        try {
            $options = @('-I','-m','app.import_station_lan','--directory',$data,'--port',"$ImportPort",'--source',$ImportSourceIp,'--confirm-station',$ConfirmStation)
            if ($ReplaceSql) { $options += '--replace' }
            Invoke-Native $python $options
        } finally {
            Remove-NetFirewallRule -Name $temporaryRule -ErrorAction SilentlyContinue
        }
    }
    'Prepare' {
        if ($registered -or (Test-Path -LiteralPath $config)) { throw 'La estación ya está preparada. Use las opciones de mantenimiento.' }
        if (!$Station -or !$Certificate -or !$PrivateKey -or !$DevicesFile) { throw 'Faltan datos de estación, TLS o registro de dispositivos.' }
        Test-Subnet $Listen $LanSubnet
        if (!$DnsName) { $DnsName = $Listen }
        if ($DnsName -notmatch '^[a-zA-Z0-9][a-zA-Z0-9.-]{0,252}$') { throw 'Nombre HTTPS no válido.' }
        $devices = Get-Content -LiteralPath $DevicesFile -Raw | ConvertFrom-Json
        $odbcRegistry = 'HKLM:\SOFTWARE\ODBC\ODBCINST.INI\ODBC Drivers'
        if (!(Get-ItemPropertyValue -LiteralPath $odbcRegistry -Name 'ODBC Driver 18 for SQL Server' -ErrorAction SilentlyContinue)) {
            if (!$AcceptOdbcLicense) { throw 'Confirme la licencia de Microsoft antes de instalar ODBC Driver 18.' }
            $odbc = Join-Path $Bundle 'msodbcsql.msi'
            $signature = Get-AuthenticodeSignature -LiteralPath $odbc
            if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch '(?:^|,\s*)O=Microsoft Corporation(?:,|$)') {
                throw 'El instalador ODBC incluido requiere firma válida de Microsoft.'
            }
            $odbcProcess = Start-Process -FilePath msiexec.exe -ArgumentList "/i ""$odbc"" /qn /norestart IACCEPTMSODBCSQLLICENSETERMS=YES" -Wait -PassThru -WindowStyle Hidden
            if ($odbcProcess.ExitCode -eq 3010) { throw 'Reinicie Windows para completar la instalación de ODBC.' }
            if ($odbcProcess.ExitCode -ne 0) { throw "Falló la instalación de ODBC ($($odbcProcess.ExitCode))." }
        }
        if (Test-Path -LiteralPath $binary) { throw 'Ya existe el directorio de programa. Verifique la preparación anterior.' }
        New-Item -ItemType Directory -Path $binary -ErrorAction Stop | Out-Null
        Protect-Folder $binary ''
        Stage-Files $binary
        New-Item -ItemType Directory -Path $data -ErrorAction Stop | Out-Null
        Protect-Folder $data ''
        New-Item -ItemType Directory -Path $logs -ErrorAction Stop | Out-Null
        Copy-Item -LiteralPath $Certificate -Destination (Join-Path $data 'server-chain.pem')
        Copy-Item -LiteralPath $PrivateKey -Destination (Join-Path $data 'server-key.pem')
        [ordered]@{station=$Station;listen=$Listen;port=$Port;subnet=$LanSubnet;dnsName=$DnsName;devices=$devices} |
            ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $config -Encoding UTF8
        Write-Wrapper
        Invoke-Native $python @('-I','-m','app.initialize_station','--directory',$data)
    }
    'Install' {
        if ($registered) { throw 'El servicio de esta estación ya existe.' }
        if ($CapturadorDatabase) { Import-Capturador }
        Invoke-Native $python @('-I','-m','app.station_service','--config',$config,'--check')
        $site = Get-Content -LiteralPath $config -Raw | ConvertFrom-Json
        Test-Subnet $site.listen $site.subnet
        Invoke-Native $wrapper @('install',$wrapperConfig)
        try {
            Invoke-Native sc.exe @('config',$service,'obj=', $principal)
            Invoke-Native sc.exe @('sidtype',$service,'unrestricted')
            Protect-Folder $binary 'ReadAndExecute'
            Protect-Folder $data 'ReadAndExecute'
            Protect-Folder $logs 'Modify'
            New-NetFirewallRule -Name $rule -DisplayName 'Zencillo Local API (LAN)' -Direction Inbound -Action Allow -Protocol TCP -LocalAddress $site.listen -LocalPort $site.port -RemoteAddress $site.subnet -Profile Domain,Private | Out-Null
            Invoke-Native sc.exe @('config',$service,'start=','auto')
            Start-Service -Name $service
            (Get-Service -Name $service).WaitForStatus('Running', [TimeSpan]::FromSeconds(25))
            Test-ApiReady $site
        } catch {
            Stop-Service -Name $service -ErrorAction SilentlyContinue
            Remove-NetFirewallRule -Name $rule -ErrorAction SilentlyContinue
            & $wrapper uninstall $wrapperConfig
            throw
        }
    }
    'Update' {
        if (!$registered) { throw 'Servicio no instalado.' }
        $release = Join-Path $binary ("updates\" + [Guid]::NewGuid().ToString("N"))
        $staged = Join-Path $release 'staged'
        $backup = Join-Path $release 'previous'
        New-Item -ItemType Directory -Path $release -Force | Out-Null
        New-Item -ItemType Directory -Path $staged,$backup -ErrorAction Stop | Out-Null
        Stage-Files $staged
        Invoke-Native (Join-Path $staged 'runtime\python.exe') @('-I','-m','app.station_service','--config',$config,'--check')
        Stop-Service -Name $service
        (Get-Service -Name $service).WaitForStatus('Stopped',[TimeSpan]::FromSeconds(25))
        $moved = @()
        $activated = @()
        try {
            foreach ($part in @('runtime','importer',"$service.exe")) {
                Move-Item -LiteralPath (Join-Path $binary $part) -Destination $backup
                $moved += $part
                Move-Item -LiteralPath (Join-Path $staged $part) -Destination $binary
                $activated += $part
            }
            Start-Service -Name $service
            (Get-Service -Name $service).WaitForStatus('Running',[TimeSpan]::FromSeconds(25))
            Test-ApiReady (Get-Content -LiteralPath $config -Raw | ConvertFrom-Json)
        } catch {
            Stop-Service -Name $service -ErrorAction SilentlyContinue
            foreach ($part in $activated) { Move-Item -LiteralPath (Join-Path $binary $part) -Destination $staged }
            foreach ($part in $moved) { Move-Item -LiteralPath (Join-Path $backup $part) -Destination $binary }
            Start-Service -Name $service
            throw
        }
        'Actualización aplicada. Se retiene previous para rollback y revisión del técnico.'
    }
    'Uninstall' {
        if ($registered) {
            Stop-Service -Name $service
            (Get-Service -Name $service).WaitForStatus('Stopped',[TimeSpan]::FromSeconds(25))
            Invoke-Native $wrapper @('uninstall',$wrapperConfig)
            Remove-NetFirewallRule -Name $rule -ErrorAction SilentlyContinue
        }
        'Configuración y credenciales conservadas.'
    }
    'Start' { Start-Service -Name $service; Test-ApiReady (Get-Content -LiteralPath $config -Raw | ConvertFrom-Json) }
    'Stop' { Stop-Service -Name $service }
}
