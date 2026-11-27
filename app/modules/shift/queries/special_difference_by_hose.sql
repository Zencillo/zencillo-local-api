SELECT
    mt.IdManguera AS IdManguera,
    ci.CodigoSurtidor AS Surtidor,
    ci.CodigoCara AS Cara,
    mt.CodigoManguera AS Manguera,
    CAST(SUM(
        CAST(fcd.Cantidad AS DECIMAL(18, 7))
        * CAST(td.Precio AS DECIMAL(18, 7))
    ) AS DECIMAL(19, 2)) AS SubtotalReferencia,
    CAST(SUM(fcd.Subtotal) AS DECIMAL(19, 2)) AS SubtotalReal
FROM dbo.FacturaCliente AS fc
INNER JOIN dbo.FacturaClienteDetalle AS fcd
    ON fcd.IdFacturaCliente = fc.IdFacturaCliente
INNER JOIN dbo.MangueraTanque AS mt
    ON mt.CodigoManguera = fc.CodigoManguera
INNER JOIN dbo.CaraIsla AS ci
    ON ci.IdCara = mt.IdCara
   AND ci.CodigoCara = fc.CodigoCara
   AND ci.CodigoIsla = fc.CodigoIsla
INNER JOIN dbo.TurnoDetalle AS td
    ON td.IdTurno = fc.IdTurno
   AND td.IdManguera = mt.IdManguera
WHERE fc.IdTurno = ?
  AND fc.precio_especial = 1
  AND fc.TipoVenta = 1
  AND ISNULL(fc.Anulada, 0) = 0
GROUP BY mt.IdManguera, ci.CodigoSurtidor, ci.CodigoCara, mt.CodigoManguera
ORDER BY ci.CodigoSurtidor, ci.CodigoCara, mt.CodigoManguera;
