SELECT TE.IdTurno, TE.Identificacion, TE.Empleado AS EmpleadoTurno,
       ISNULL(PE.Codigo, '') AS CodigoEmpleado, JZ.Empleado AS EmpleadoJornadaZeta, CONVERT(NVARCHAR(MAX), TE.XMLApertura) AS XMLApertura
FROM dbo.TurnoEmpleado AS TE
LEFT JOIN dbo.PermisosEmpleado AS PE ON PE.Identificacion = TE.Identificacion
LEFT JOIN dbo.JornadaZeta AS JZ ON JZ.Fecha = TE.FechaZeta AND JZ.Abierta = 1
WHERE TE.Isla = ? AND TE.Abierto = 1 AND EXISTS (
    SELECT 1 FROM dbo.ConfiguracionInicial AS CI
    WHERE CI.CodigoIsla = TE.Isla AND CI.IdCompania = ? AND CI.IdCentroVenta = ?
);
