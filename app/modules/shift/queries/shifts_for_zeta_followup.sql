SELECT
    IdTurno, FechaZeta, Isla, Fecha, HoraApertura, HoraCierre, Abierto,
    Identificacion, SincronizoApertura, SincronizoCierre, XMLApertura, XMLCierre,
    NumeroDeTurno, SincronizoLecturasIniciales, SincronizoLecturasFinales,
    ContrasenaEmpleado, Empleado
FROM dbo.TurnoEmpleado WITH(NOLOCK)
WHERE FechaZeta = ? AND Isla = ?
ORDER BY Isla, NumeroDeTurno DESC;
