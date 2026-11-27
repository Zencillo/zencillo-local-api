UPDATE F SET CodigoElectronico = ? FROM dbo.FacturaCliente AS F
WHERE F.IdFacturaCliente = ? AND F.CodigoIsla = CONVERT(VARCHAR(20), ?)
AND EXISTS (SELECT 1 FROM dbo.ConfiguracionInicial
            WHERE IdCompania = ? AND IdCentroVenta = ? AND CodigoIsla = ?);
