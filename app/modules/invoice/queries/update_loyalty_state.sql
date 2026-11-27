UPDATE L SET Estado = ? FROM dbo.FacturaClienteFidelizada AS L
    INNER JOIN dbo.FacturaCliente AS F ON F.IdFacturaCliente = L.IdFacturaCliente
WHERE F.IdFacturaCliente = ? AND F.CodigoIsla = CONVERT(VARCHAR(20), ?)
    AND EXISTS (
      SELECT 1 FROM dbo.ConfiguracionInicial AS C
      WHERE C.IdCompania = ? AND C.IdCentroVenta = ? AND C.CodigoIsla = ?
    );
