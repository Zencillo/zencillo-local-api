UPDATE
    C
SET
    Estado = ?
FROM
    dbo.CheckVentasEstacion AS C
WHERE
    C.IdVentaEstacion = ?
AND C.CodigoIsla      = CONVERT(VARCHAR(20), ?)
AND EXISTS
    (
        SELECT
            1
        FROM
            dbo.ConfiguracionInicial
        WHERE
            IdCompania    = ?
        AND IdCentroVenta = ?
        AND CodigoIsla    = ?);