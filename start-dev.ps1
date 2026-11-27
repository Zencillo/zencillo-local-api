param(
    [ValidateRange(1024, 65535)]
    [int]$Port = 8765
)

$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    throw 'No se encontro el Python de .venv. Consulta README.md.'
}

Push-Location -LiteralPath $PSScriptRoot
try {
    & $python -c "import jwt, pyodbc, uvicorn; from app.main import create_app; create_app()"
    if ($LASTEXITCODE -ne 0) {
        throw 'Revisa las dependencias de pyproject.toml y la configuracion local.'
    }
    Write-Host "Swagger: http://127.0.0.1:${Port}/docs"
    & $python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port $Port
    if ($LASTEXITCODE -ne 0) {
        throw "Uvicorn no pudo iniciar o se detuvo con error. Revisa la salida y el puerto $Port."
    }
} finally {
    Pop-Location
}
