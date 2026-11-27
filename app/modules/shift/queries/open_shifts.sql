SELECT
    [IdTurno], [FechaZeta], [Isla], [Fecha], [HoraApertura], [HoraCierre],
    [Abierto], [TurnoEmpleado].[Identificacion], [SincronizoApertura],
    [SincronizoCierre], [XMLApertura], [XMLCierre], [NumeroDeTurno],
    [SincronizoLecturasIniciales], [SincronizoLecturasFinales],
    [SincronizoTotalOperaciones], [TurnoEmpleado].[Empleado],
    [ContrasenaEmpleado], [FechaCierre],
    ISNULL(PE.Codigo, '') AS CodigoEmpleado
FROM [dbo].[TurnoEmpleado] WITH(NOLOCK)
LEFT JOIN PermisosEmpleado AS PE WITH(NOLOCK)
    ON PE.Identificacion = TurnoEmpleado.Identificacion
WHERE Isla IN ({{ISLAS}}) AND Abierto = 1;
