INSERT dbo.HistorialPreset (Cantidad, Hora, Cara, Tipo, IdTurno, Producto)
SELECT ?, ?, ?, ?, T.IdTurno, ?
FROM dbo.TurnoEmpleado AS T
WHERE T.IdTurno = ? AND T.Isla = ?
  AND EXISTS (SELECT 1 FROM dbo.ConfiguracionInicial
              WHERE IdCompania = ? AND IdCentroVenta = ? AND CodigoIsla = ?);
