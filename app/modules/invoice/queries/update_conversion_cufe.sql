UPDATE D SET CodigoElectronico = ? FROM dbo.FacturaClienteConversion AS D JOIN dbo.FacturaCliente AS F ON F.IdFacturaCliente = D.IdFacturaCliente
WHERE F.IdFacturaCliente = ? AND F.CodigoIsla = CONVERT(VARCHAR(20), ?)
AND EXISTS (SELECT 1 FROM dbo.ConfiguracionInicial
            WHERE IdCompania = ? AND IdCentroVenta = ? AND CodigoIsla = ?);
