UPDATE P SET XMLFacturacion = ?, XMLFidelizacion = ?, XMLConsolidacion = ?,
    IdFactura = COALESCE(CAST(? AS int), IdFactura)
FROM dbo.ControlProcesosPorVenta AS P
WHERE P.IdVenta = ? AND P.Isla = ? AND P.IdCentroVenta = ?
    AND EXISTS (SELECT 1 FROM dbo.ConfiguracionInicial AS C
                WHERE C.CodigoIsla = P.Isla AND C.IdCentroVenta = P.IdCentroVenta AND C.IdCompania = ?);
