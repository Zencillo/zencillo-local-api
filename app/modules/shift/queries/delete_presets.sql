DELETE FROM HistorialPreset
    WHERE HistorialPreset.IdTurno = ? AND EXISTS (SELECT 1 FROM dbo.TurnoEmpleado WHERE IdTurno = HistorialPreset.IdTurno AND Isla = ?);
