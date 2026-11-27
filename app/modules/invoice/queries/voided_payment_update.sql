UPDATE FPD SET Anulada = 1
FROM dbo.FormaPagoDetalle FPD
INNER JOIN dbo.Venta V ON V.IdVenta = FPD.IdVenta
INNER JOIN dbo.TurnoEmpleado T ON T.IdTurno = V.IdTurno
INNER JOIN dbo.ConfiguracionPOS P ON P.CodigoIsla = T.CodigoIsla
WHERE FPD.IdVenta = ? AND P.CodigoIsla = ? AND P.IdCompania = ?
  AND P.IdCentroVenta = ? AND T.CodigoIsla = ?;
