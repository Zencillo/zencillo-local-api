SELECT
    CaraIsla.IdIsla AS IdIsla,
    CaraIsla.CodigoIsla AS CodigoIsla,
    CaraIsla.IdSurtidor AS IdSurtidor,
    CaraIsla.CodigoSurtidor AS CodigoSurtidor,
    CaraIsla.ModoCara AS ModoCara,
    CaraIsla.IdCara AS IdCara,
    CaraIsla.CodigoCara AS CodigoCara,
    MangueraTanque.CodigoManguera AS CodigoManguera,
    MangueraTanque.IdManguera AS IdManguera,
    MangueraTanque.IdCombustible AS IdCombustible,
    MangueraTanque.Descripcion AS Descripcion,
    Articulo.IdArticulo AS IdArticulo,
    Articulo.Articulo AS Articulo,
    Combustible.CodigoArticulo AS CodigoArticulo,
    MangueraTanque.Precio AS Precio
FROM
    MangueraTanque WITH(NOLOCK),
    CaraIsla WITH(NOLOCK),
    Combustible WITH(NOLOCK),
    Articulo WITH(NOLOCK)
WHERE
    MangueraTanque.IdCara = CaraIsla.IdCara
    AND Combustible.IdCombustible = MangueraTanque.IdCombustible
    AND Articulo.CodigoArticulo = Combustible.CodigoArticulo
    AND CaraIsla.CodigoIsla = ?
ORDER BY
    CaraIsla.CodigoCara ASC,
    MangueraTanque.CodigoManguera ASC;
