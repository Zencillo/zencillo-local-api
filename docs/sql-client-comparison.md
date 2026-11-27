# Comparación de clientes SQL Server DEMO

TCP a 10.1.10.15:1433 verificado desde Windows. pyodbc 5.2.0 detecta Driver 17 y 18. El entorno virtual contiene pymssql 2.3.13 con FreeTDS 1.4.27, instalado solo para diagnóstico. pip check aprobó. No se realizó login sin credenciales. El 08001 del Driver 18 es el fallo reportado, aún sin mensaje técnico completo.

| Alternativa | Estado autenticado | Configuración del comparador |
|---|---|---|
| pyodbc + ODBC 18 | 08001 reportado, pendiente de reproducir | Encrypt=yes y TrustServerCertificate=no. CA confiable en Windows. HostNameInCertificate opcional con nombre confirmado. |
| pyodbc + ODBC 17 | Pendiente | Mismos valores de cifrado y validación. Usar el DNS del certificado si la IP no figura en él. El comparador exige que ese DNS resuelva exclusivamente a DEMO. |
| pymssql + FreeTDS | Pendiente | Cifrado require, PEM de CA y verificación del nombre con configuración temporal. Se omite sin CA explícita. |

Desde PowerShell en la raíz del proyecto, con el PEM de la CA de confianza y el DNS del certificado confirmados por el administrador:

~~~powershell
.\.venv\Scripts\python.exe -m tools.compare_sql_clients --certificate-name "DNS-DEL-CERTIFICADO" --ca-file "C:\ruta\ca-demo.pem"
~~~

Ejecutar preferentemente con una cuenta de diagnóstico de permisos mínimos. Usar una consola real con el trazado ODBC deshabilitado. El comparador lee la conexion DEMO de .env, conserva los mensajes técnicos de las excepciones con credenciales redactadas y solo envía SELECT DB_NAME(), @@VERSION. No guarda el resultado ni modifica la conexión de FastAPI. Sin parámetros en la línea de comando, compara los ODBC contra la IP y deja FreeTDS pendiente.

Un 08001 por sí solo no identifica si el problema es la cadena de confianza, el nombre o una incompatibilidad de negociación. Comparar con cifrado obligatorio en ambos ODBC. Si el servidor solo funciona relajando TLS, cualquier prueba excepcional requerirá autorización explícita y un plan que considere suplantación de servidor y exposición de credenciales. La sección Excepción DEMO describe el modo diagnóstico explícito.

## Certificado observado durante PRELOGIN

El diagnóstico tools.inspect_demo_tls negoció TLS 1.2 sin enviar LOGIN7 ni credenciales. El contexto estricto de Python rechazó un certificado autofirmado. La inspección posterior, también sin login, observó CN e issuer SSL_Self_Signed_Fallback, sin SAN, SHA-256 f6d6fe2e8d269b87e6ba586ef07070d585301ec1c8eb0c02456223a3331f5b16. La huella observada no implica confianza ni debe importarse como CA.

### Excepción DEMO

El comparador ahora puede ofrecer --allow-unverified-demo, con confirmación local DEMO SIN VALIDAR. La excepción se limita al destino DEMO fijo, exige cifrado y omite validación de identidad. Solo se ofrece para errores clasificados como TLS o cuando queda pendiente la CA de FreeTDS. No es apta para producción; un intermediario podría recibir credenciales. Usar una cuenta de diagnóstico de mínimo privilegio. Los mensajes 08001 sin causa específica se conservan como fallo de conexión, no como prueba de TLS.

Para la configuración definitiva, el administrador debe asignar a SQL Server un certificado de servidor emitido por una CA aprobada con SAN que corresponda al DNS autorizado, o SAN IP si se conecta por IP. Instalar la cadena de confianza en Windows para ODBC y proporcionar el PEM de CA a FreeTDS. Luego repetir el login con validación habilitada. No se cambió la configuración de FastAPI.

## Resultado autenticado en DEMO

El comparador confirmó DB_NAME() = ZencilloAutomatizacion y Microsoft SQL Server 2025 RTM (17.0.1000.7), Standard Developer Edition, mediante SELECT DB_NAME(), @@VERSION.

| Cliente | TLS con validación | Excepción DEMO con cifrado y sin validar identidad |
|---|---|---|
| ODBC 18 | Falló con 08001 y -2146893019: cadena de certificación no confiable | Login y SELECT correctos |
| ODBC 17 | Falló con 08001 y -2146893019: cadena de certificación no confiable | Login y SELECT correctos |
| pymssql / FreeTDS | Omitido por falta del PEM de la CA | Login y SELECT correctos |

Se comprobó compatibilidad de los tres clientes bajo la excepción, sin validar la identidad del servidor. Este resultado no habilita su uso en producción. Mantener ODBC 18 como primera opción para repetir la prueba cuando SQL Server presente un certificado de confianza con SAN correcto. FastAPI conserva su configuración. El diagnóstico no ejecutó otros SELECT ni realizó escrituras.

Para ejecución no interactiva, el comparador recupera la credencial DEMO del .env local. Ver configuración única y parámetros TLS en [validación SQL](sql-validation.md). Las credenciales no se toman de informes.
