SELECT
      MangueraTanque.IdManguera AS IdManguera,
      MangueraTanque.CodigoManguera AS CodigoManguera,
      MangueraTanque.IdCara AS IdCara,
      CaraIsla.IdIsla AS IdIsla,
      CaraIsla.CodigoIsla AS CodigoIsla,
      Combustible.CodigoArticulo AS CodigoArticulo,
      CaraIsla.Descripcion AS Descripcion
    FROM
      Articulo,
      CaraIsla,
      Combustible,
      MangueraTanque
    WHERE
      Combustible.IdCombustible = MangueraTanque.IdCombustible
      AND Articulo.CodigoArticulo = Combustible.CodigoArticulo
      AND CaraIsla.IdCara = MangueraTanque.IdCara
  AND (? = 0 OR (Articulo.IdArticulo = ? AND CaraIsla.CodigoIsla = ?))
