# Informe de pruebas y límites

Windows, Python 3.12.10. La instalación del paquete con pip install ".[test]" y la ejecución de python -m pytest -q finalizaron correctamente.

Resultado: **15 pruebas aprobadas**. Una advertencia de deprecación en el TestClient de Starlette por un alias de AnyIO.

La prueba unitaria comprueba el hash local. Las pruebas HTTP en proceso cubren emisión JWT, secreto incorrecto, token ausente o inválido, estación incorrecta, dispositivo sin permiso, operación desconocida, rechazo de SQL como identificador, parámetros extra o de tipo inválido, filas y lista vacía, conversión Decimal a entero, Unicode, NULL, error ODBC, timeout, formato de errores y cierre de cursores y conexiones. Todas las llamadas SQL usan dobles de prueba.

Antes de integrar Flutter:

1. Instalar manualmente el SP en una base de pruebas y verificar versión mínima del motor, esquema dbo, aliases, permisos EXEC, conexión ODBC cifrada y SQLSTATE reales.
2. Comparar filas y semántica vacía del piloto con el batch legado en Android y Windows. El SELECT no establece orden.
3. Acordar provisión y rotación local de credenciales, CA, certificados y límites de tamaño y tasa en el proxy. Verificar renovación y revocación operativa. Los cambios al registro en variables de entorno requieren reinicio.
4. Probar HTTPS extremo a extremo en una red de pruebas. El cifrado de aplicación adicional está diseñado y pendiente de decidir e implementar.
5. Aprobar el adaptador Flutter y la bandera por estación en la siguiente fase.

El script no se ejecutó en SQL Server. La compatibilidad SQL Server 2008 indicada en README es por inspección sintáctica. No se inició ni instaló un servicio.

## Validación del arranque de desarrollo

Python 3.12.10, puerto loopback 8765. GET /docs y /openapi.json devolvieron HTTP 200 por red y el esquema incluyó ambos endpoints POST. POST /v1/auth/token devolvió 200 para los dos dispositivos de desarrollo y 401 para secreto incorrecto. POST /v1/operations devolvió 401 con token inválido, 403 sin permiso, 404 con operación desconocida, 400 con parámetros adicionales o solicitud inválida y 503 DATABASE_NOT_CONFIGURED con la operación válida. El texto de validación y el sobre de error se compararon exactamente.

pytest -v: 16 aprobadas, con la advertencia de Starlette/AnyIO previamente observada. pip check: sin requisitos rotos. Detectados drivers ODBC 17, 18 y SQL Server. Sin conexión SQL ni instalación de SP.
