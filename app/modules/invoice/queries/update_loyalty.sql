UPDATE F SET Fidelizada = ? FROM dbo.FacturaCliente AS F
WHERE F.IdFacturaCliente = ? AND F.CodigoIsla = CONVERT(VARCHAR(20), ?)
    AND EXISTS (
      SELECT 1 FROM dbo.ConfiguracionInicial AS C
      WHERE C.IdCompania = ? AND C.IdCentroVenta = ? AND C.CodigoIsla = ?
    );
