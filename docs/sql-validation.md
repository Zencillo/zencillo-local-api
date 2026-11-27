# Piloto SQL Server â€” SELECT legado

## DecisiÃ³n vigente

Flutter Capturador â†’ FastAPI â†’ SQL Server existente. Zencillo Cloud mantiene su propio transporte y sus propias credenciales. El backend registra identificadores `Query`, valida `parameters` con tipos y ejecuta SQL interno fijo con parÃ¡metros ODBC `?` para cualquier valor recibido. Para los procedimientos ya instalados se conservan firma, orden de resultados y efectos. No se crea ni altera el esquema desde esta migraciÃ³n.

`ListarTiposVehiculo` acepta `parameters: {}` y ejecuta exactamente:

~~~sql
SELECT idtipovehiculo, tipovehiculo FROM tipo_vehiculo
~~~

Devuelve HTTP 200 con `data.items`, nombres originales y valores SQL convertidos a sus tipos JSON. El SELECT no garantiza orden. El script 001 quedÃ³ obsoleto, conservado como historial enteramente comentado y excluido del despliegue. No se instalÃ³ en DEMO.

## Reproducir

En PowerShell, desde la raÃ­z del proyecto:

~~~powershell
.\.venv\Scripts\python.exe -m tools.run_demo_pilot --report ".env.demo-direct-$([guid]::NewGuid().ToString('N')).txt"
~~~

El diagnÃ³stico apunta a DEMO (10.1.10.15:1433, ZencilloAutomatizacion). Solicita contraseÃ±a sin eco, valida la base y que `tipo_vehiculo` resuelve a `dbo.tipo_vehiculo`. Obtiene la referencia ODBC y abre FastAPI temporal en loopback con credenciales y JWT en memoria. Obtiene JWT por HTTP, valida los campos exactos, tipos y valores del JSON contra el multiconjunto SQL, y exige 19 filas para esta referencia. Si el catÃ¡logo cambia durante la prueba, repetir en un intervalo estable. No imprime filas ni credenciales.

TLS con validaciÃ³n es el valor predeterminado. Para una prueba DEMO excepcional, agregar `--allow-unverified-demo` y confirmar localmente con `DEMO SIN VALIDAR` cuando ODBC reporte el fallo TLS. El cifrado se mantiene, pero la identidad del servidor no se verifica. No trasladar esta excepciÃ³n a la configuraciÃ³n de servicio. El despliegue requiere un certificado con SAN correcto y una cadena confiable en Windows, y una cuenta SQL con permiso SELECT Ãºnicamente sobre los catÃ¡logos necesarios.

## Lecturas candidatas para la siguiente fase

| OperaciÃ³n existente | Referencia en Capturador | Equivalencia a comprobar |
|---|---|---|
| CatÃ¡logo de tipos de gasto | ArticleApi.getGastoTipo â†’ GastoTipoBD.readQuery | Lista, alias y tipos originales, vacÃ­o y filtros por ID si se exponen. |
| ConfiguraciÃ³n de redondeo | ArticleApi.getConfigRedondeo â†’ ConfiguracionRedondeo.selectQuery | PrecisiÃ³n y nulos, defaults en el DTO y consulta equivalente dentro del batch. |
| CatÃ¡logo de combustibles | ArticleApi.getCombustible â†’ CombustibleBD.selectQuery | CÃ³digos como texto y alias originales, lista vacÃ­a y duplicados. Es una lectura distinta de combustibles por cara. |
| Combustibles por cara | Bloque COMBUSTIBLE_CARA de DataRepository | Mantener cruces, cÃ³digos de cara y orden de resultSets si se migra junto al batch. Dejar para despuÃ©s de las lecturas simples. |

Preservar por consumidor listas, objetos, booleanos, mensajes, nulos y orden de resultSets. Los cambios en ventas, facturaciÃ³n, pagos y cierres requieren etapas de compatibilidad e idempotencia propias.

## Resultado real confirmado en DEMO

ODBC 18 con validación devolvió 08001 por cadena no confiable. Con la excepción DEMO confirmada en consola, el SELECT directo devolvió 19 filas reales (int, texto). POST /v1/auth/token y POST /v1/operations devolvieron HTTP 200. Los campos y tipos JSON coincidieron exactamente con el contrato y las 19 filas coincidieron con ODBC sin depender del orden. No se ejecutó DDL ni DML. Pytest: 16 aprobadas y una advertencia de deprecación Starlette/AnyIO. Pip check: sin requisitos rotos.

## Configuracion local automatica

Los diagnosticos leen LOCAL_API_SQL_CONNECTION del .env de este proyecto. El archivo
esta excluido por .gitignore y contiene secretos locales. Si alguna vez se aprovisiona
una instalacion nueva con la variable vacia, ejecutar una vez
`python -m tools.demo_config --setup-sa`. La entrada se oculta y se guarda con ODBC
Driver 18 y validacion de certificado. Para produccion debe usarse una cuenta de
minimo privilegio y un certificado confiable.

El .env conserva validacion TLS. La excepcion se activa solo para DEMO en memoria
con --allow-unverified-demo --confirm-demo-exception despues de un fallo TLS.

## Fase 6 — Catálogos de Capturador

Las operaciones ListarTiposGasto, ListarConfiguracionRedondeo y ListarCombustibles están registradas con parámetros vacíos y permisos independientes. Corresponden a ArticleApi.getGastoTipo, getConfigRedondeo y getCombustible. Ejecutan los SELECT originales y devuelven data.items. El gasto conserva estado=1. El redondeo conserva la bandera como entero y factor como número. Los códigos de artículo se preservan como texto. Los DTO proyectan los campos consumidos por Flutter, preservan NULL y serializan fechas ISO. No se añadieron SP ni escrituras.

Para comparar ODBC y HTTP real sin prompts, usar:

~~~powershell
.\.venv\Scripts\python.exe -m tools.run_phase6_demo --report docs/demo-phase6-report.json --allow-unverified-demo --confirm-demo-exception
~~~

Esas opciones autorizan para esta ejecución la excepción de DEMO únicamente después de un fallo TLS. La conexión y el JWT temporal quedan en memoria. El informe indica el modo TLS y compara el multiconjunto de valores sin imprimir registros. El nombre de salida debe ser nuevo.

Validación de esta ejecución: 21 pruebas aprobadas y pip check limpio. TCP 10.1.10.15:1433 accesible. El almacén del usuario efectivo de Codex no devolvió la entrada específica ZencilloLocalApi/SQL-DEMO/10.1.10.15:1433/ZencilloAutomatizacion. Por eso no se abrió una sesión SQL en esta fase y los tres conteos y las respuestas HTTP con datos reales quedan pendientes. Verificar nombre de destino y perfil de Windows sin compartir contraseñas.


### Evidencia final DEMO

El flujo se ejecuto sin prompts y confirmo HTTP 200 con 7 tipos de gasto, 11
configuraciones de redondeo y 2 combustibles. Nombres, tipos y valores coincidieron
con los SELECT originales sin depender del orden. DEMO devuelve Documento y
FactorRedondeo como enteros. El DTO conserva esos enteros y admite las formas
texto y decimal ya contempladas. ODBC 18 estricto devolvio 08001 por cadena no
confiable. El reintento DEMO con cifrado sin validacion fue autorizado y ocurrio
solo en memoria. pytest: 23 aprobadas y una advertencia de Starlette/AnyIO.
pip check: sin requisitos rotos. Ver [informe](demo-phase6-final.json).

## Regresion modular

Las 23 pruebas previas pasaron antes de agregar cinco pruebas de recursos,
rechazo de entradas no registradas y enlace de parametros. El total final fue
28 aprobadas y pip check sin requisitos rotos. El wheel limpio incluyo los
cuatro SQL y se pudo importar y leer desde fuera del checkout sin .env.

Se repitieron los cuatro SELECT y las cuatro peticiones autenticadas, con
HTTP 200 y equivalencia por multiconjunto de campos, tipos y valores:
vehiculos 19, tipos de gasto 7, configuraciones de redondeo 11, combustibles 2.
ODBC 18 con TLS validado devolvio 08001 por cadena no confiable. La excepcion
confirmada permitio el cotejo solo en DEMO, cifrado sin validacion de identidad.
Ver [evidencia](demo-modular-equivalence.json).
