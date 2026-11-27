DECLARE @Ids XML = ?;
SELECT FPD.*, FC.IdFacturaCliente, FC.IdDocumento, FC.IdTurno AS IdTurno_Fa,
  FC.IdTipoDocumento, FC.CodigoIsla, FC.Fecha, FC.HoraEntrega,
  FC.IdentificacionCliente, FC.NombreCliente, FC.IdResolucion,
  FC.PrefijoFactura, FC.NumeroFactura, FC.IdFormaPago AS IdFormaPago_Fa,
  FC.FormasPago, FC.Placa, FC.Kilometraje, FC.TotalIVAS, FC.Subtotal,
  FC.ValorTotalFactura, FC.PorcentajeDescuento, FC.ValorDescuento,
  FC.Propina, FC.TotalICE, FC.ValorTotalSinSubsidioECU, FC.AhorroPorSubsidioECU,
  FC.RecaudoSUIC, FC.TotalaPagar, FC.CodigoElectronico, FC.CodigoCara,
  FC.CodigoManguera, FC.IdVentaEstacion, FC.SecuenciaVenta, FC.PuntosAcumulados,
  FC.FechaProximaRevicion, FC.TipoVenta AS TipoVenta_Fa, FC.TipoFactura,
  FC.TipoEmision, FC.Facturada, FC.Fidelizada, FC.Impresa,
  FC.DatosImpresionFactura, FC.IdentificacionConductor, FC.NombreConductor,
  FC.IdentPasaporte, FC.TotalFleet
FROM dbo.FormaPagoDetalle FPD WITH (NOLOCK)
INNER JOIN dbo.FacturaCliente FC WITH (NOLOCK)
  ON FC.IdDocumento = FPD.IdVenta AND FC.IdTurno = FPD.IdTurno
INNER JOIN dbo.TurnoEmpleado TE WITH (NOLOCK) ON TE.IdTurno = FC.IdTurno
WHERE (? IS NULL OR FPD.IdVenta = ?) AND (? IS NULL OR FPD.IdTurno = ?)
  AND (@Ids IS NULL OR FPD.IdVenta IN (
    SELECT N.value('.', 'INT') FROM @Ids.nodes('/Ids/Id') T(N)))
  AND ? IS NOT NULL AND ? IS NOT NULL AND ? IS NOT NULL AND TE.Isla = ?
ORDER BY FPD.IdVenta DESC;
