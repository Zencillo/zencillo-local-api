[CmdletBinding()]
param([string]$StationFile, [switch]$Preview, [switch]$HostConfirmed, [ValidateSet('Install','Verify','Rollback')][string]$Mode = 'Install')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
function Select-File([string]$Title, [string]$Filter) {
    $picker = New-Object System.Windows.Forms.OpenFileDialog
    try {
        $picker.Title = $Title
        $picker.Filter = $Filter
        if ($picker.ShowDialog() -ne 'OK') { throw 'Selección cancelada.' }
        return $picker.FileName
    } finally { $picker.Dispose() }
}

function Assert-StationOrigin($Site) {
    if ($Site.dnsName -notmatch '^[a-zA-Z0-9][a-zA-Z0-9.-]{0,252}$') { throw 'El nombre HTTPS no es válido.' }
    $local = @([Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces() |
        Where-Object OperationalStatus -eq Up | ForEach-Object {
            $_.GetIPProperties().UnicastAddresses | ForEach-Object { $_.Address.IPAddressToString }
        })
    if ($Site.listen -notin $local) {
        throw 'La IPv4 configurada no está activa en este equipo. Revise si cambió la IP de la estación.'
    }
    try {
        $resolved = @([Net.Dns]::GetHostAddresses($Site.dnsName) |
            Where-Object AddressFamily -eq InterNetwork | ForEach-Object IPAddressToString | Select-Object -Unique)
    } catch { throw 'El nombre HTTPS no resuelve. Revise DNS.' }
    if ($resolved.Count -ne 1 -or $resolved[0] -ne $Site.listen) {
        throw 'El nombre HTTPS debe resolver a la IPv4 configurada de este equipo.'
    }
}

function Require-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { return }
    $launcher = Join-Path $PSScriptRoot 'Install-Station.ps1'
    $arguments = '-NoProfile -File "{0}" -Mode {1} -HostConfirmed' -f $launcher,$Mode
    if ($StationFile) { $arguments += ' -StationFile "{0}"' -f $StationFile }
    try {
        $child = Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') -ArgumentList $arguments -Verb RunAs -Wait -PassThru
        exit $child.ExitCode
    } catch { throw 'La operación requiere privilegios de administrador y no se autorizó.' }
}

function Invoke-PilotRequest([string]$Uri, [string]$Body, [hashtable]$Headers) {
    try {
        Invoke-RestMethod -Method Post -Uri $Uri -Body $Body -Headers $Headers -ContentType 'application/json' -MaximumRedirection 0 -TimeoutSec 15 -ErrorAction Stop
    } catch {
        $errorRecord = $_
        $response = $errorRecord.Exception.Response
        $id = if ($response) { $response.Headers['X-Request-ID'] }
        $reference = if ($id -match '^[a-f0-9]{32}$') { " Referencia $id." } else { '' }
        $message = switch ([int]$response.StatusCode) {
            401 { 'La sesión no fue aceptada. Vuelva a autenticar el dispositivo.' }
            403 { 'El dispositivo no tiene permiso para este catálogo.' }
            503 {
                $trace = if ($reference) {
                    Get-ChildItem -LiteralPath (Join-Path $env:ProgramData 'ZencilloLocalApi\logs') -File -Filter '*.log' -ErrorAction SilentlyContinue |
                        Select-String -SimpleMatch "request_id=$id" | Select-Object -Last 1 -ExpandProperty Line
                }
                if ($trace -match 'category=login_rejected|sqlstate=28000') {
                    'SQL rechazó la credencial del perfil importado.'
                } elseif ($trace -match 'category=certificate') {
                    'SQL rechazó la confianza del certificado. Revise la cadena y el nombre SQL.'
                } else { 'SQL no está disponible. Revise el servidor y el puerto SQL.' }
            }
            504 { 'SQL excedió el tiempo de espera. Revise la conectividad.' }
            default {
                if ($errorRecord.Exception.Status -in @('TrustFailure','SecureChannelFailure')) {
                    'Windows no pudo validar HTTPS. Revise el nombre y la CA aprobada.'
                } else { 'La API no respondió. Revise el servicio, la dirección y la red.' }
            }
        }
        throw "$message$reference"
    }
}

function Test-RunningStation {
    $info = Get-CimInstance Win32_Service -Filter "Name='ZencilloLocalApi'"
    if (!$info -or $info.State -ne 'Running') { throw 'El servicio Local API está detenido o no está registrado.' }
    $sitePath = Join-Path $env:ProgramData 'ZencilloLocalApi\service.json'
    $site = Get-Content -LiteralPath $sitePath -Raw -Encoding UTF8 | ConvertFrom-Json
    Assert-StationOrigin $site
    $account = 'NT SERVICE\ZencilloLocalApi'
    if ($info.StartName -ne $account -or $info.StartMode -ne 'Auto') {
        throw 'La identidad o el arranque automático del servicio no coincide con el perfil esperado.'
    }
    $listener = @(Get-NetTCPConnection -State Listen -LocalAddress $site.listen -LocalPort $site.port -ErrorAction SilentlyContinue)
    if ($listener.Count -ne 1) { throw 'No se encontró un único ejecutor escuchando en la dirección configurada.' }
    $listenerPid = $listener[0].OwningProcess
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$listenerPid"
    $python = Join-Path $env:ProgramFiles 'ZencilloLocalApi\runtime\python.exe'
    if (!$process -or $process.ExecutablePath -ne $python -or $process.ParentProcessId -ne $info.ProcessId) {
        throw 'El puerto está abierto, pero no pertenece al ejecutor de este servicio.'
    }
    $expectedSid = ([Security.Principal.NTAccount]::new($account)).Translate([Security.Principal.SecurityIdentifier]).Value
    $owner = Invoke-CimMethod -InputObject $process -MethodName GetOwnerSid
    if ($owner.ReturnValue -ne 0 -or $owner.Sid -ne $expectedSid) {
        throw 'No se pudo acreditar el propietario real del ejecutor.'
    }

    $origin = "https://$($site.dnsName):$($site.port)"
    $credential = Get-Credential -Message 'Introduzca el identificador y secreto de un dispositivo piloto. No utilice la credencial SQL.'
    if (!$credential) { throw 'Verificación cancelada.' }
    $payload = @{device_id=$credential.UserName;secret=$credential.GetNetworkCredential().Password} | ConvertTo-Json -Compress
    try { $login = Invoke-PilotRequest "$origin/v1/auth/token" $payload @{} }
    finally { $payload = $null; $credential = $null }
    if (!$login.success -or !$login.data.access_token) { throw 'La API no emitió una sesión válida.' }
    $headers = @{Authorization="Bearer $($login.data.access_token)"}
    $counts = foreach ($operation in 'ListarTiposVehiculo','ListarTiposGasto','ListarConfiguracionRedondeo','ListarCombustibles') {
        $payload = @{Query=$operation;parameters=@{}} | ConvertTo-Json -Compress
        $result = Invoke-PilotRequest "$origin/v1/operations" $payload $headers
        if (!$result.success -or $result.data.items -isnot [array]) { throw "Respuesta inesperada en $operation." }
        "$operation = $($result.data.items.Count) filas"
    }

    $boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
    $body = @("URL: $origin", "Cuenta: $account", "Arranque Windows: $boot",
        "Inicio del proceso: $($process.CreationDate)", 'DPAPI y conexión SQL comprobados por los cuatro catálogos.') + $counts
    [void][System.Windows.Forms.MessageBox]::Show(($body -join [Environment]::NewLine), 'Verificación Local API')
}

try {
    & (Join-Path $PSScriptRoot 'Test-StationBundle.ps1')
    if ($Mode -ne 'Install') {
        if ($Preview) { "Vista previa $Mode sin cambios."; exit 0 }
        if ($Mode -eq 'Rollback' -and !$HostConfirmed -and [System.Windows.Forms.MessageBox]::Show(
            'Se detendrá y retirará Local API. Se conservará el perfil SQL protegido.',
            'Revertir Local API','YesNo') -ne 'Yes') { exit 0 }
        Require-Administrator
        if ($Mode -eq 'Verify') { Test-RunningStation; exit 0 }
        $registered = Get-CimInstance Win32_Service -Filter "Name='ZencilloLocalApi'"
        $wrapper = Join-Path $env:ProgramFiles 'ZencilloLocalApi\ZencilloLocalApi.exe'
        if ($registered -and $registered.PathName -notlike ('"' + $wrapper + '"*') -and $registered.PathName -ne $wrapper) {
            throw 'El servicio registrado no corresponde a este paquete. Se requiere revisión administrativa.'
        }
        & (Join-Path $PSScriptRoot 'Manage-StationService.ps1') -Action Uninstall -Apply -Confirm:$false
        [void][System.Windows.Forms.MessageBox]::Show('Servicio retirado. Perfil conservado.', 'Local API')
        exit 0
    }
    if (!$StationFile) {
        $StationFile = Select-File 'Abrir configuración de la estación' 'Configuración de estación (*.json)|*.json'
    }
    $StationFile = (Resolve-Path -LiteralPath $StationFile).Path
    $site = Get-Content -LiteralPath $StationFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $base = Split-Path -Parent $StationFile
    function Site-Path([string]$Path) {
        if (![IO.Path]::IsPathRooted($Path)) { $Path = Join-Path $base $Path }
        return (Resolve-Path -LiteralPath $Path).Path
    }
    $database = $null
    if ($site.capturadorDatabase) {
        $database = Site-Path $site.capturadorDatabase
    } else {
        $locations = @(
            (Join-Path $env:ProgramFiles 'Capturador\db'),
            (Join-Path $env:ProgramFiles 'ZencilloCapturador\db'),
            (Join-Path $env:SystemDrive 'Capturador\db'),
            (Join-Path (Split-Path -Parent $PSScriptRoot) 'db')
        )
        $found = @($locations | Select-Object -Unique | Where-Object {
            Test-Path -LiteralPath (Join-Path $_ 'default.isar') -PathType Leaf
        })
        if ($found.Count -eq 1) {
            $database = $found[0]
        } else {
            $database = Split-Path -Parent (Select-File 'Seleccione default.isar del Capturador autorizado' 'Base de Capturador (default.isar)|default.isar')
        }
    }
    if (!(Test-Path -LiteralPath (Join-Path $database 'default.isar') -PathType Leaf)) {
        throw 'La carpeta indicada no contiene la configuración existente.'
    }
    $options = @{
        Action = 'Setup'
        Bundle = $PSScriptRoot
        Station = [string]$site.station
        Listen = [string]$site.listen
        DnsName = [string]$site.dnsName
        LanSubnet = [string]$site.lanSubnet
        Certificate = Site-Path $site.certificate
        PrivateKey = Site-Path $site.privateKey
        DevicesFile = Site-Path $site.devicesFile
        CapturadorDatabase = $database
    }
    if ($site.port) { $options.Port = [int]$site.port }
    $manager = Join-Path $PSScriptRoot 'Manage-StationService.ps1'
    if ($Preview) { & $manager @options -WhatIf; exit }
    if (!$site.dnsName) { $site | Add-Member -NotePropertyName dnsName -NotePropertyValue $site.listen -Force }
    Assert-StationOrigin $site
    $port = if ($options.Port) { $options.Port } else { 8765 }
    $url = "https://$($site.dnsName):$port"
    $summary = @("Estación: $($site.station)", "Equipo: $env:COMPUTERNAME", "IPv4: $($site.listen)",
                 "URL para Windows y Android: $url", '¿Instalar en este equipo autorizado?') -join [Environment]::NewLine
    if (!$HostConfirmed -and [System.Windows.Forms.MessageBox]::Show($summary,'Confirmar equipo','YesNo') -ne 'Yes') { exit 0 }
    Require-Administrator
    $options.AcceptOdbcLicense = $false
    $isInstalled = Get-ItemPropertyValue -LiteralPath 'HKLM:\SOFTWARE\ODBC\ODBCINST.INI\ODBC Drivers' -Name 'ODBC Driver 18 for SQL Server' -ErrorAction SilentlyContinue
    if (!$isInstalled) {
        $options.AcceptOdbcLicense = [System.Windows.Forms.MessageBox]::Show(
            'Para continuar debe aceptar los términos de Microsoft ODBC Driver 18. Consulte los términos aprobados por su organización.',
            'Instalación de ODBC', 'YesNo') -eq 'Yes'
        if (!$options.AcceptOdbcLicense) { throw 'Se necesita la aprobación de ODBC Driver 18.' }
    }
    & $manager @options -Apply -Confirm:$false
    [void][System.Windows.Forms.MessageBox]::Show(("Servicio iniciado. URL compartida: $url" + [Environment]::NewLine + "Para comprobar las lecturas SQL, utilice Verificar."), 'Zencillo Local API')
} catch {
    [void][System.Windows.Forms.MessageBox]::Show($_.Exception.Message, 'Zencillo Local API')
    exit 1
}
