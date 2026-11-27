UPDATE VC SET Estado = ?, TipoEnvio = ?
FROM dbo.VentasCupo VC
INNER JOIN dbo.TurnoEmpleado TE ON TE.IdTurno = VC.IdTurno
WHERE VC.IdVentaEstacion = ? AND ? IS NOT NULL AND ? IS NOT NULL
  AND ? IS NOT NULL AND TE.Isla = ?;
