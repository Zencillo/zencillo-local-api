# Zencillo Local API

Servicio local Python/FastAPI independiente. Requiere Python 3.12 y, en estación, un controlador ODBC de SQL Server compatible con el motor. La aplicación solo ejecuta el SELECT fijo del piloto.

## Instalación y pruebas (PowerShell)

~~~powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install ".[test]"
.\.venv\Scripts\python.exe -m pytest
~~~

## Configuración de una estación de pruebas

Inyectar mediante el gestor de secretos de la estación:

| Variable | Contenido |
|---|---|
| LOCAL_API_STATION | Identificador único de estación, configurado por el instalador. |
| LOCAL_API_JWT_KEY | Secreto local de alta entropía, al menos 32 bytes. Distinto por estación y ajeno a Cloud. |
| LOCAL_API_CONFIG_DIR | Directorio del perfil externo de estación para el factory. Por defecto se utiliza el directorio de .env. |
| LOCAL_API_DEVICES | JSON que mapea ID de dispositivo a station, secret_hash, operations y enabled opcional. |
| LOCAL_API_TOKEN_SECONDS | TTL, por defecto 300, máximo 900. |
| LOCAL_API_SQL_TIMEOUT | Segundos para conexión y comando, por defecto 5. |

Para aprovisionar un dispositivo, generar un secreto de alta entropía y guardarlo en el dispositivo por un canal privado. Generar su hash sin pasarlo por argumentos ni historial:

~~~powershell
.\.venv\Scripts\python.exe -c "from getpass import getpass; from app.core.security import hash_secret; print(hash_secret(getpass('Secreto local: ')))"
~~~

Forma del registro (marcadores, sin secretos):

~~~json
{"dispositivo-1":{"station":"estacion-prueba","secret_hash":"<hash-generado>","operations":["ListarTiposVehiculo"]}}
~~~

Con las variables configuradas y certificado de estación válido:

~~~powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8443 --ssl-certfile <certificado> --ssl-keyfile <clave>
~~~

Para dispositivos remotos, el administrador configura interfaz privada o proxy TLS, confianza de CA, límites de tamaño y tasa de solicitudes de autenticación. No exponer un listener HTTP en la LAN. Los cambios de permisos se cargan al reiniciar el proceso. La rotación de la clave JWT invalida tokens anteriores. El cifrado adicional está descrito en [el diseño versionado](docs/encryption.md).

## Contrato

- POST /v1/auth/token recibe device_id y secret. Devuelve el sobre de éxito con access_token, token_type y expires_in.
- POST /v1/operations requiere Authorization Bearer. JSON: {"Query":"ListarTiposVehiculo","parameters":{}}.
- Ã‰xito HTTP 200 con data.items, incluso vacío. Error con success=false, data=null y error.code; 400 validación, 401 autenticación, 403 autorización, 404 operación no registrada, 503 SQL no disponible, 504 timeout y 500 fallo interno.

## Consulta SQL del catálogo

El piloto usa el SELECT existente de Capturador: `SELECT idtipovehiculo, tipovehiculo FROM tipo_vehiculo`. No requiere instalar objetos. El script 001 es histórico y obsoleto. La consulta conserva los dos campos originales y no impone orden. [Guía de validación](docs/sql-validation.md).

Modelo de salida con los nombres originales, entero y texto, conservando NULL si el origen lo devuelve. Capturador podrá aplicar sus defaults cuando se implemente el adaptador.

## Desarrollo local en Windows sin SQL Server

Las dependencias se instalan desde pyproject.toml con el entorno .venv existente. El arranque lee .env en la raíz en UTF-8. Las variables del proceso tienen prioridad. Usa .env.example como plantilla. JWT, estación y dispositivos son obligatorios. Sin un perfil de estación válido las operaciones SQL devuelven HTTP 503 DATABASE_NOT_CONFIGURED.

Desde cualquier carpeta de PowerShell:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\dev\zencillo_local_api\start-dev.ps1
~~~

Swagger: http://127.0.0.1:8765/docs. Para otro puerto local, agrega -Port al comando. El arranque usa el modo factory y escucha únicamente en loopback. El Swagger predeterminado carga sus recursos visuales desde CDN.

El servidor busca el archivo externo `AUTOMATIZACION.security_zen` junto a `service.json` o en `LOCAL_API_CONFIG_DIR` si se inicia el factory. El lector existente usa `legacy-sql-key.dpapi` en ese directorio. El archivo se entrega externamente. Las utilidades DEBUG seleccionan DEMO de forma explícita y pueden usar `LOCAL_API_SQL_CONNECTION` en sus pruebas. El runtime normal no usa esta variable como origen SQL.

La configuración generada en esta máquina usa dos dispositivos locales, uno con permiso al piloto y otro sin él. Los secretos de esos dispositivos están en .env.dev-credentials.json, archivo privado e ignorado, separado del registro de hashes de .env. No adjuntarlos ni compartirlos.

## Consultas por dominio

El modulo app/modules/article contiene el repositorio, los DTO, el registro de
sus cuatro operaciones y los recursos SQL en queries/. El registro comun,
la conexion ODBC y la seguridad viven en app/core. El cargador acepta
unicamente miembros del enum interno y lee recursos empaquetados mediante
importlib.resources. Una solicitud HTTP solo aporta el identificador registrado
y parametros validados. Las cuatro operaciones actuales no reciben parametros.
Para futuras consultas, el adaptador ODBC enlaza valores por separado de SQL.

El wheel incluye queries/*.sql mediante package-data. Construir desde un
checkout limpio y distribuir el wheel con la configuracion local aprovisionada
por separado.

## Aprovisionamiento por estación Windows

El receptor `app.install_station_sql` está preparado para uso local desde un
instalador elevado. El proceso padre confirma compañía, centro e isla y envía
el perfil de Capturador mediante su entrada estándar privada. El receptor
valida el destino por ODBC 18 con TLS estricto y `SELECT DB_NAME()`, rechaza
`sa` y guarda el perfil en Windows Credential Manager bajo la identidad que
ejecutó el proceso. No se crean objetos SQL.

Para repetir el piloto con SQL DEMO y HTTPS verificado en Flutter, usar
`python -m tools.run_flutter_windows_pilot --allow-demo-sql-exception --native-windows`
o `--android` con el emulador dedicado `emulator-5570`. La excepción se aplica
al certificado de SQL DEMO. El cliente Flutter valida el certificado de HTTPS
con la CA efímera del piloto.

## Servicio Windows permanente

[Servicio Windows por estación](windows/README.md). Incluye el paquete offline, la importación SQL local o remota, el aprovisionamiento de dispositivos y el mantenimiento administrativo.
