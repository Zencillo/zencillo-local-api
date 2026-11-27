SELECT TOP (?) FC.IdFacturaCliente, FC.CodigoCara, FC.FormasPago, FC.IdDocumento,
  FC.ValorTotalFactura - ISNULL(FC.ValorDescuento, 0) AS ValorTotalFactura,
  ISNULL(FC.NumeroFactura, '') AS NumeroFactura, CPV.IdVenta,
  CPV.CambioFormaPagoVenta, FC.TipoVenta, FC.IdFormaPago,
  ISNULL(FC.PrefijoFactura, '') AS PrefijoFactura,
  ISNULL(FC.IdentificacionCliente, '') AS IdentificacionCliente,
  ISNULL(FC.Fidelizada, 0) AS Fidelizada
FROM dbo.ControlProcesosPorVenta CPV WITH (NOLOCK)
INNER JOIN dbo.FacturaCliente FC WITH (NOLOCK)
  ON CPV.IdVenta = FC.IdDocumento AND CPV.IdTurno = FC.IdTurno
INNER JOIN dbo.TurnoEmpleado TE WITH (NOLOCK) ON TE.IdTurno = FC.IdTurno
WHERE FC.IdTurno = ? AND CPV.CambioFormaPagoVenta = 0 AND CPV.TipoVenta <> 2
  AND FC.IdFormaPago <> 6 AND ISNULL(FC.Anulada, 0) <> 1
  AND ISNULL(FC.panterapago, 0) = 0
  AND ? IS NOT NULL AND ? IS NOT NULL AND ? IS NOT NULL AND TE.Isla = ?
ORDER BY CPV.IdVenta DESC;
