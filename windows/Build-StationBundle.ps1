[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Destination,
    [Parameter(Mandatory)][string]$PythonZip,
    [Parameter(Mandatory)][string]$PythonZipHash,
    [Parameter(Mandatory)][string]$Wheelhouse,
    [Parameter(Mandatory)][string]$WinSW,
    [Parameter(Mandatory)][string]$WinSWHash,
    [Parameter(Mandatory)][string]$WinSWLicense,
    [Parameter(Mandatory)][string]$ImporterBuild,
    [Parameter(Mandatory)][string]$OdbcMsi,
    [Parameter(Mandatory)][string]$BuildPython
)

$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $Destination) { throw 'El destino del paquete debe ser nuevo.' }
foreach ($pair in @(@($PythonZip,$PythonZipHash), @($WinSW,$WinSWHash))) {
    if ((Get-FileHash -LiteralPath $pair[0] -Algorithm SHA256).Hash -ne $pair[1]) {
        throw 'Un archivo de distribución no coincide con el SHA-256 aprobado.'
    }
}
$signature = Get-AuthenticodeSignature -LiteralPath $OdbcMsi
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch '(?:^|,\s*)O=Microsoft Corporation(?:,|$)') {
    throw 'ODBC debe venir firmado por Microsoft.'
}
if (!(Test-Path -LiteralPath (Join-Path $ImporterBuild 'CapturadorWindows.exe'))) {
    throw 'Compile el asistente Windows con el target main_local_api_import.dart.'
}
if (!(Test-Path -LiteralPath (Join-Path $ImporterBuild 'data\flutter_assets'))) {
    throw 'Incluya el directorio completo del ejecutable Flutter.'
}
$runtime = Join-Path $Destination 'runtime'
New-Item -ItemType Directory -Path $Destination | Out-Null
Expand-Archive -LiteralPath $PythonZip -DestinationPath $runtime
$isolated = @(Get-ChildItem -LiteralPath $runtime -Filter 'python312._pth')
if ($isolated.Count -ne 1 -or !(Test-Path -LiteralPath (Join-Path $runtime 'python.exe'))) {
    throw 'Se requiere CPython 3.12 embebible x64.'
}
$site = Join-Path $runtime 'site-packages'
& $BuildPython -m pip install --platform win_amd64 --python-version 3.12 --only-binary ':all:' --no-compile --no-index --find-links $Wheelhouse --target $site 'zencillo-local-api==0.1.0'
if ($LASTEXITCODE -ne 0) { throw 'No se pudo ensamblar el runtime desde los wheels de release.' }
$isolatedLines = Get-Content -LiteralPath $isolated[0].FullName
@($isolatedLines | Where-Object { $_ -eq 'python312.zip' }) + @('.', 'site-packages') |
    Set-Content -LiteralPath $isolated[0].FullName -Encoding ascii
& (Join-Path $runtime 'python.exe') -B -I -c 'from app.modules.article.repository import ArticleQuery, load_query; import app.station_service, app.install_station_sql, app.import_station_lan, app.core.local_envelope, app.core.security_zen, pyodbc; from app.modules.license.operations import LicenseQuery, load_license_query; from app.modules.shift.operations import ShiftQuery, load_shift_query; from app.modules.client.operations import load_client_queries; from app.modules.price.operations import load_price_queries; assert all(load_price_queries()) and all(load_client_queries()) and all(load_shift_query(query) for query in ShiftQuery) and all(load_query(query) for query in ArticleQuery) and all(load_license_query(query) for query in LicenseQuery)'
if ($LASTEXITCODE -ne 0) { throw 'Falló la verificación del runtime embebido.' }
Copy-Item -LiteralPath $WinSW -Destination (Join-Path $Destination 'WinSW.exe')
Copy-Item -LiteralPath $OdbcMsi -Destination (Join-Path $Destination 'msodbcsql.msi')
$importer = Join-Path $Destination 'importer'
$flutterData = Join-Path $importer 'data'
$assets = Join-Path $flutterData 'flutter_assets'
New-Item -ItemType Directory -Path $assets -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $ImporterBuild 'CapturadorWindows.exe') -Destination $importer
Get-ChildItem -LiteralPath $ImporterBuild -File -Filter '*.dll' | Copy-Item -Destination $importer
foreach ($name in @('app.so','icudtl.dat')) {
    Copy-Item -LiteralPath (Join-Path (Join-Path $ImporterBuild 'data') $name) -Destination $flutterData
}
foreach ($name in @('AssetManifest.bin', 'FontManifest.json', 'NOTICES.Z', 'NativeAssetsManifest.json','fonts','shaders')) {
    $source = Join-Path (Join-Path $ImporterBuild 'data\flutter_assets') $name
    if (Test-Path -LiteralPath $source) { Copy-Item -LiteralPath $source -Destination $assets -Recurse }
}
Copy-Item -LiteralPath $WinSWLicense -Destination (Join-Path $Destination 'WinSW-License.txt')
foreach ($name in @('Manage-StationService.ps1','Test-StationBundle.ps1','Install-Station.ps1','Instalar.cmd','README.md')) {
    $source = Join-Path $PSScriptRoot $name
    if ($name.EndsWith('.ps1')) {
        [IO.File]::WriteAllText((Join-Path $Destination $name),[IO.File]::ReadAllText($source),[Text.UTF8Encoding]::new($true))
    } else {
        Copy-Item -LiteralPath $source -Destination $Destination
    }
}
(Get-FileHash -LiteralPath (Join-Path $Destination 'WinSW.exe') -Algorithm SHA256).Hash |
    Set-Content -LiteralPath (Join-Path $Destination 'WinSW.sha256') -Encoding ascii
$root = (Resolve-Path -LiteralPath $Destination).Path
$entries = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force | Sort-Object FullName | ForEach-Object {
    [ordered]@{path=$_.FullName.Substring($root.Length+1).Replace('\','/');bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
})
[ordered]@{format=1;files=$entries} | ConvertTo-Json -Depth 5 |
    Set-Content -LiteralPath (Join-Path $root 'bundle-manifest.json') -Encoding UTF8
& (Join-Path $PSScriptRoot 'Test-StationBundle.ps1') -Bundle $root
'Paquete preparado sin certificados, credenciales ni archivos .env.'
