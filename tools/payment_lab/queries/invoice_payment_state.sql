SELECT fc.IdFormaPago, fc.ValorTotalFactura, fc.FormasPago,
       fp.IdCompania, fp.IdCentroVenta, fp.CodigoCara, fp.IdUltimaVenta,
       CONVERT(nvarchar(max), fp.XMLConsolidador),
       CONVERT(nvarchar(max), fp.XMLFactura), fp.Sincronizada, fp.CodigoIsla
FROM dbo.FacturaCliente AS fc WITH (UPDLOCK, HOLDLOCK)
LEFT JOIN dbo.FormaPagoVenta AS fp WITH (UPDLOCK, HOLDLOCK)
  ON fp.IdDocumento = fc.IdDocumento AND fp.IdTurno = fc.IdTurno
WHERE fc.IdFacturaCliente = ? AND fc.IdDocumento = ? AND fc.IdTurno = ?
  AND EXISTS (
      SELECT 1 FROM dbo.ConfiguracionInicial
      WHERE IdCompania = ? AND IdCentroVenta = ? AND CodigoIsla = ?
  );
