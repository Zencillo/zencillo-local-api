# Instalación de Zencillo Local API por estación

## Paquete offline Windows x64

Extraiga el ZIP aprobado en una carpeta de distribución protegida. Compruebe su SHA-256 por el canal de release y ejecute Instalar.cmd en el host Windows autorizado y elija Instalar. El asistente confirma estación, nombre del equipo, IPv4 y URL antes de solicitar UAC; luego muestra la URL común para Windows y Android. El instalador valida el manifiesto interno y solicita el archivo JSON de estación, preparado fuera del paquete. El JSON requiere station, listen, dnsName, lanSubnet, certificate, privateKey y devicesFile. port es opcional, 8765 por defecto. capturadorDatabase es opcional. Las rutas de archivos pueden ser relativas al JSON. No guarde credenciales SQL en ese JSON.

El asistente busca default.isar en ubicaciones habituales y junto al directorio de distribución. Si encuentra varios, o ninguno, pide seleccionar el archivo. Luego muestra compañía, centro, isla, servidor y base antes de hacer la importación. Instalar.cmd usa el runtime incorporado y reutiliza ODBC 18 si ya está registrado. Si falta, el técnico debe aceptar los términos de Microsoft antes de que se ejecute el MSI incluido. La instalación de ODBC no se revierte al retirar Local API porque otras aplicaciones pueden usarlo.

Para previsualizar sin cambios, ejecute Install-Station.ps1 -StationFile <ruta-json> -Preview. Para estaciones donde el Capturador está en otro equipo Windows, use el flujo Receive de esta guía. La importación sigue ocurriendo por HTTPS temporal y no requiere copiar el Isar.

El menú Verificar solicita privilegios para inspeccionar la identidad real del proceso y la configuración protegida. Con una credencial individual de dispositivo piloto, prueba los cuatro catálogos por HTTPS y muestra conteos, cuenta Windows, hora de arranque y hora de inicio del proceso. Capture una evidencia antes del reinicio y otra después. Para acreditar independencia de la sesión del técnico, no inicie sesión tras reiniciar hasta que un cliente autorizado de la LAN confirme la API. Esta verificación no solicita la contraseña SQL.

Revertir detiene y retira Local API y su regla. Conserva el perfil cifrado. Use LEGACY_SQL para volver al transporte anterior. Si FastAPI está en otro Windows, use Receive según la sección remota y verifique con el mismo menú.

## Construcción para release

El equipo de release genera el wheelhouse con Build-StationWheelhouse.ps1 en un directorio de compilación nuevo. Luego ejecuta Build-StationBundle.ps1 con CPython 3.12 embebible x64, WinSW 3 en modo empaquetado, ODBC 18 x64 firmado por Microsoft, un wheelhouse aprobado con Zencillo Local API y sus dependencias, y el directorio completo del asistente Flutter compilado desde lib/main_local_api_import.dart. El paquete no incluye perfiles SQL, JWT, certificados ni .env. La compilación debug sirve para laboratorio. El MSI oficial seleccionado es ODBC 18.7.1.1 x64, que incluye el redistribuible Visual C++. El paquete conserva los avisos de CPython, WinSW, Flutter y los metadatos de licencia de los wheels. [ODBC de Microsoft](https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver18).

El servicio usa una cuenta virtual Windows propia. [Configuración XML de WinSW](https://github.com/winsw/winsw/blob/v3/docs/xml-config-file.md) y [cuentas virtuales de Windows](https://learn.microsoft.com/es-es/windows/win32/api/winsvc/nf-winsvc-changeserviceconfigw).

## Preparación de una estación

1. Identificar DNS, IPv4 fija y subred privada. Conseguir la cadena y clave PEM del servidor. El certificado debe cubrir el nombre o IP del origen. Windows y Android deben confiar en la CA. La regla operativa limita IP de escucha, puerto y subred en los perfiles Domain y Private.
2. Registrar cada dispositivo con un secreto aleatorio distinto. El operador captura el secreto en los campos ocultos. El JSON de registro contiene solo hashes y permisos.

~~~powershell
.\runtime\python.exe -I -m app.enroll_station_device --registry C:\Instalacion\dispositivos.json --device caja-windows
.\runtime\python.exe -I -m app.enroll_station_device --registry C:\Instalacion\dispositivos.json --device caja-android
~~~

3. En el host autorizado, cerrar Capturador, seleccionar su carpeta db y ejecutar el instalador elevado. Usar la misma versión de esquemas en el asistente y en el Capturador instalado. Conservar el respaldo operativo del almacenamiento. Reemplazar los valores ilustrativos de este ejemplo.

~~~powershell
$params = @{
    Action = 'Setup'
    Station = 'eds-piloto'
    Listen = '192.168.20.10'
    DnsName = 'api.eds-piloto.example.invalid'
    LanSubnet = '192.168.20.0/24'
    Certificate = 'C:\Instalacion\server-chain.pem'
    PrivateKey = 'C:\Instalacion\server-key.pem'
    DevicesFile = 'C:\Instalacion\dispositivos.json'
    CapturadorDatabase = 'C:\Capturador\db'
}
.\Manage-StationService.ps1 @params -WhatIf
~~~

Tras autorizar, repetir con -Apply en lugar de -WhatIf. Si el equipo no tiene ODBC 18 y el técnico está autorizado a aceptar sus términos, añadir -AcceptOdbcLicense. El asistente pide confirmar la estación, instancia o puerto y base que detectó. El receptor comprueba SQL con ODBC 18 y TLS estricto, y guarda el perfil bajo DPAPI de equipo y ACL del servicio. Install arranca el servicio y verifica /healthz por HTTPS. Los Capturadores comparten el origen y mantienen credenciales distintas. Validar los cuatro catálogos de cada dispositivo con la cuenta de menor privilegio disponible.

## Capturador en otro equipo Windows

En el host del servicio preparar TLS y la LAN con Prepare. Ejecutar Receive con -ImportSourceIp, -ConfirmStation, -ImportPort 8766 y -Apply. El prompt oculto pide una invitación aleatoria URL-safe de 32 a 128 caracteres, compartida por el canal privado autorizado.

~~~powershell
Set-Location .\importer
.\CapturadorWindows.exe C:\Capturador\db --remote https://api.eds-piloto.example.invalid:8766
~~~

Ejecutar el asistente anterior en el Capturador Windows de origen con la app cerrada. Confirmar el origen e introducir la invitación en el campo oculto. El receptor comprueba la IPv4 autorizada, consume la invitación y valida SQL desde el host. Deja de escuchar tras una transferencia o al pasar cinco minutos. Ejecutar Install -Apply en el host. El puerto operativo, el temporal y el de SQL son independientes. El origen de la importación puede ser otro Windows. Originarla desde un Android requiere integrar el adaptador con el contexto administrativo de esa app.

## Mantenimiento

- Status, Start y Stop controlan el servicio. Start verifica HTTPS.
- Import o Receive con -ReplaceSql valida el reemplazo antes de guardar. Reiniciar el servicio para usar el perfil nuevo.
- Update -Bundle <ruta> -WinSWHash <sha256 aprobado> -Apply conserva el perfil y los archivos TLS. Verifica el runtime antes de detener el servicio y comprueba HTTPS después del arranque. Retiene los binarios anteriores y revierte si falla la activación.
- Uninstall -Apply retira el servicio y la regla operativa. Conserva los archivos y credenciales.
- Los logs rotados se escriben en %ProgramData%\ZencilloLocalApi\logs. Para actualizar devices, hacer copia del archivo privado y reemplazar su registro de hashes desde una sesión administrativa. Reiniciar para cargarlo.

El registro de servicio, cambio de identidad, acceso efectivo a DPAPI como servicio, reinicio automático, actualización y retirada se deben completar en una VM autorizada antes de distribuir. El repositorio tiene código y pruebas de laboratorio, más el generador del paquete.
