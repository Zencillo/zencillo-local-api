SELECT
      Articulo.IdArticulo,
      Articulo.IdTarifaIVA,
      Articulo.IdPresentacion,
      Articulo.CodigoArticulo,
      Articulo.CodigoAlterno,
      Articulo.PrecioAbierto,
      Articulo.IncluyeIVA,
      Articulo.Articulo,
      Articulo.NombreCorto,
      Articulo.Precio,
      Articulo.Presentacion,
      Articulo.PresentacionUnidades,
      Articulo.Porcentaje,
      Articulo.CodigoICE,
      Articulo.PorcentajeICE,
      Articulo.Combustible,
      Articulo.Estado,
      Articulo.ImpuestoValorFijo,
      CASE 
        WHEN E.IdArticulo IS NULL THEN 0
        ELSE 1
      END AS ExisteRegistro,
      ISNULL(E.Saldo, 0) AS Existencia
    FROM Articulo WITH(NOLOCK)
    LEFT JOIN articuloexistencia_pv E
      ON Articulo.IdArticulo = E.IdArticulo
     AND E.idPuntoVenta = ?
    WHERE Articulo.Articulo = Articulo.Articulo
      AND Articulo.CodigoArticulo = Articulo.CodigoArticulo
      AND ISNULL(Articulo.Combustible, 0) = ?
      AND Articulo.Estado = Articulo.Estado
    ORDER BY Articulo.CodigoArticulo ASC
