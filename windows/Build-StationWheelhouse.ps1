[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$BuildPython,
    [Parameter(Mandatory)][string]$Wheelhouse,
    [Parameter(Mandatory)][string]$StagingDirectory
)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $StagingDirectory) { throw 'Use un directorio nuevo para la compilación.' }
$project = Split-Path -Parent $PSScriptRoot
$source = Join-Path $project 'app'
New-Item -ItemType Directory -Path $StagingDirectory | Out-Null
$stage = (Resolve-Path -LiteralPath $StagingDirectory).Path
Copy-Item -LiteralPath (Join-Path $project 'pyproject.toml') -Destination $stage
Get-ChildItem -LiteralPath $source -Recurse -File | Where-Object Extension -in @('.py','.sql') | ForEach-Object {
    $relative = $_.FullName.Substring($source.Length+1)
    $target = Join-Path (Join-Path $stage 'app') $relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath $_.FullName -Destination $target
}
& $BuildPython -m pip wheel --wheel-dir $Wheelhouse $stage
if ($LASTEXITCODE -ne 0) { throw 'No se pudo construir el wheelhouse de estación.' }
