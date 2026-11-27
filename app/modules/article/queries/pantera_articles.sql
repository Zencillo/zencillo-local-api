SELECT
      IdArticulo, IdTarifaIVA, IdPresentacion, CodigoArticulo, CodigoAlterno,
      PrecioAbierto, IncluyeIVA, Articulo, NombreCorto, Precio,
      Presentacion, PresentacionUnidades, Porcentaje, CodigoICE,
      PorcentajeICE, Combustible, Estado, ImpuestoValorFijo
    FROM Articulo WITH(NOLOCK)
    WHERE CodigoArticulo IN (
      'PANTERA_PAGO_PINES',
      'PANTERA_PAGO_RECARGAS',
      'PANTERA_PAGO_RECAUDOS',
      'PANTERA_PAGO_APUESTAS',
      'PANTERA_PAGO_PAQUETES'
    )
    ORDER BY CodigoArticulo ASC
