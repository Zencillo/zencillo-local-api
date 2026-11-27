SELECT Identificacion, ContrasenaEmpleado AS ClaveTurno FROM dbo.TurnoEmpleado
WHERE IdTurno = ? AND Isla = ? AND Abierto = 1 AND Identificacion = ?;
