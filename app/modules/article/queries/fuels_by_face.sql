SELECT
  CaraIsla.IdCara AS IdCara,
  MangueraTanque.IdCombustible AS IdCombustible,
  Combustible.IdArticulo AS IdArticuloCombustible,
  Combustible.Nombre AS Nombre,
  MangueraTanque.Precio AS Precio,
  Combustible.Color AS Color,
  CaraIsla.CodigoCara,
  MangueraTanque.CodigoManguera AS CodigoManguera,
  Combustible.CodigoArticulo AS CodigoCombustible,
  MangueraTanque.IdManguera AS IdManguera,

  -- Campos de Articulo
  Articulo.IdArticulo,
  Articulo.IdTarifaIVA,
  Articulo.IdPresentacion,
  Articulo.CodigoArticulo,
  Articulo.CodigoAlterno,
  Articulo.PrecioAbierto,
  Articulo.IncluyeIVA,
  Articulo.Articulo,
  Articulo.NombreCorto,
  Articulo.Precio AS 'PrecioArticulo',
  Articulo.Presentacion,
  Articulo.PresentacionUnidades,
  Articulo.Porcentaje,
  Articulo.CodigoICE,
  Articulo.PorcentajeICE,
  Articulo.Combustible,
  Articulo.Estado,
  Articulo.ImpuestoValorFijo,
  Articulo.imprimir_nombre_corto

FROM
  CaraIsla WITH(NOLOCK)
  INNER JOIN MangueraTanque WITH(NOLOCK) ON CaraIsla.IdCara = MangueraTanque.IdCara
  INNER JOIN Combustible WITH(NOLOCK) ON Combustible.IdCombustible = MangueraTanque.IdCombustible
  INNER JOIN Articulo WITH(NOLOCK) ON Combustible.CodigoArticulo = Articulo.CodigoArticulo
