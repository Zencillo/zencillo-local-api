INSERT dbo.NotaCredito (IdFacturaCliente,Prefijo,NumeroNotaCredito,NumeroAutorizacion,Fecha)
SELECT F.IdFacturaCliente, ?, ?, ?, CONVERT(datetime, ?, 120)
FROM dbo.FacturaCliente AS F
WHERE F.IdFacturaCliente = ? AND F.CodigoIsla = CONVERT(VARCHAR(20), ?)
AND EXISTS (SELECT 1 FROM dbo.ConfiguracionInicial
            WHERE IdCompania = ? AND IdCentroVenta = ? AND CodigoIsla = ?);
