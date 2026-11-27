[CmdletBinding()]
param([string]$Bundle = $PSScriptRoot)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path -LiteralPath $Bundle).Path
$manifestPath = Join-Path $root 'bundle-manifest.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$items = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
$actual = @{}
foreach ($item in $items) {
    if ($item.FullName -eq $manifestPath) { continue }
    $relative = $item.FullName.Substring($root.Length+1).Replace('\','/')
    $actual[$relative] = $item
}
if ($manifest.format -ne 1 -or $manifest.files.Count -ne $actual.Count) {
    throw 'El contenido del paquete difiere del manifiesto.'
}
foreach ($entry in $manifest.files) {
    $item = $actual[$entry.path]
    if (!$item -or $item.Length -ne $entry.bytes -or
        (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash -ne $entry.sha256) {
        throw "Archivo faltante o alterado: $($entry.path)"
    }
    $actual.Remove($entry.path)
}
'Integridad local del paquete verificada.'
