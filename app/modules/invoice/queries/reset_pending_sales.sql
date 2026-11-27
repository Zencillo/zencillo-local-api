UPDATE C SET Estado = 0
FROM dbo.CheckVentasEstacion AS C
JOIN dbo.Venta AS V ON V.IdTurno = C.IdTurno AND V.CodigoVenta = C.IdVentaEstacion
WHERE V.Estado = 'Finalizada' AND C.Estado IN (9,2) AND C.CodigoIsla = CONVERT(VARCHAR(20), ?)
AND EXISTS (SELECT 1 FROM dbo.ConfiguracionInicial WHERE IdCompania = ? AND IdCentroVenta = ? AND CodigoIsla = ?);
