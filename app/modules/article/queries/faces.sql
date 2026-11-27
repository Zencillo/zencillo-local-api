SELECT
      [IdCara],
      [CodigoCara],
      [ModoCara],
      [Descripcion],
      [IdSurtidor],
      [CodigoSurtidor],
      [IdIsla],
      [CodigoIsla],
      [POS],
      [Totalizadores],
      [NumeroCapturador]
    FROM [CaraIsla]
WHERE (? = 1 OR IdIsla = ?) AND (? <= 0 OR NumeroCapturador = ?)
