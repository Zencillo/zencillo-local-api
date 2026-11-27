@echo off
setlocal
echo Zencillo Local API - estacion piloto
echo [I] Instalar  [V] Verificar  [R] Revertir  [S] Salir
choice /C IVRS /N /M "Seleccione una opcion: "
if errorlevel 4 exit /b 0
if errorlevel 3 goto rollback
if errorlevel 2 goto verify
set "stationMode=Install"
goto run
:rollback
set "stationMode=Rollback"
goto run
:verify
set "stationMode=Verify"
:run
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -File "%~dp0Install-Station.ps1" -Mode "%stationMode%"
set "installerStatus=%ERRORLEVEL%"
if not "%installerStatus%"=="0" pause
exit /b %installerStatus%
