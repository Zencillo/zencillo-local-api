SELECT H.IdHistorialPreset, H.Cantidad, H.Hora, H.Cara, H.Tipo, H.IdTurno, H.Producto
FROM dbo.HistorialPreset H
INNER JOIN dbo.TurnoEmpleado T ON T.IdTurno = H.IdTurno
INNER JOIN dbo.ConfiguracionPOS P ON P.CodigoIsla = T.CodigoIsla
WHERE (? IS NULL OR H.IdTurno = ?) AND P.CodigoIsla = ?
  AND P.IdCompania = ? AND P.IdCentroVenta = ? AND T.CodigoIsla = ?;
