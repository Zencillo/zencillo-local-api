SELECT
    TurnoEmpleado.IdTurno AS IdTurno,
    TurnoEmpleado.FechaZeta AS FechaZeta,
    TurnoEmpleado.Isla AS Isla,
    TurnoEmpleado.Fecha AS Fecha,
    TurnoEmpleado.HoraApertura AS HoraApertura,
    TurnoEmpleado.HoraCierre AS HoraCierre,
    TurnoEmpleado.Abierto AS Abierto,
    TurnoEmpleado.Identificacion AS Identificacion,
    TurnoEmpleado.SincronizoApertura AS SincronizoApertura,
    TurnoEmpleado.SincronizoCierre AS SincronizoCierre,
    TurnoEmpleado.XMLApertura AS XMLApertura,
    TurnoEmpleado.XMLCierre AS XMLCierre,
    TurnoEmpleado.NumeroDeTurno AS NumeroDeTurno,
    TurnoEmpleado.SincronizoLecturasIniciales AS SincronizoLecturasIniciales,
    TurnoEmpleado.SincronizoLecturasFinales AS SincronizoLecturasFinales,
    TurnoEmpleado.ContrasenaEmpleado AS ContrasenaEmpleado,
    TurnoEmpleado.Empleado AS Empleado
FROM TurnoEmpleado WITH(NOLOCK)
WHERE TurnoEmpleado.FechaZeta = ?
  AND (? IS NULL OR TurnoEmpleado.Isla = ?)
  AND (? = 0 OR TurnoEmpleado.Abierto = 1)
ORDER BY TurnoEmpleado.Isla, TurnoEmpleado.NumeroDeTurno DESC
