SELECT Identificacion AS identificacion, Empleado, Capturador, JornadaZeta,
       Turno AS turno, Clave, Reimpresion AS reimpresion, Calibracion, ReporteX, Codigo
FROM dbo.PermisosEmpleado
WHERE Identificacion = ?;
