SELECT 
    TurnoDetalle.IdTurnoDetalle AS IdTurnoDetalle,
    TurnoDetalle.IdTurno AS IdTurno,
    TurnoDetalle.IdManguera AS IdManguera,
    TurnoDetalle.LecturaInicial AS LecturaInicial,
    TurnoDetalle.LecturaFinal AS LecturaFinal,
    TurnoDetalle.LecturaDiferencia AS LecturaDiferencia,
    TurnoDetalle.Precio AS Precio,
    CaraIsla.CodigoSurtidor AS Surtidor,
    MangueraTanque.CodigoManguera AS Manguera,
    Combustible.Nombre AS Articulo,
    CaraIsla.CodigoCara AS Cara,
    Combustible.IdCombustible AS IdCombustible,
    isnull(AcumuladoraArticulo.Cantidad,0) AS VolumenCalibracion,
    isnull(AcumuladoraArticulo.Valor,0) AS ValorCalibracion,
    isnull(AcumuladoraArticulo.CantidadVentas,0) AS CantidadVentasCalibracion
FROM TurnoDetalle WITH(NOLOCK)
    LEFT JOIN MangueraTanque WITH(NOLOCK)
      ON TurnoDetalle.IdManguera = MangueraTanque.IdManguera
    LEFT JOIN CaraIsla WITH(NOLOCK)
      ON CaraIsla.IdCara = MangueraTanque.IdCara
    LEFT JOIN Combustible WITH(NOLOCK)
      ON Combustible.IdCombustible = MangueraTanque.IdCombustible
      LEFT JOIN
      AcumuladoraArticulo WITH(NOLOCK)
      ON AcumuladoraArticulo.IdTurno = TurnoDetalle.IdTurno
      and AcumuladoraArticulo.CodigoManguera = MangueraTanque.CodigoManguera
      AND AcumuladoraArticulo.Calibracion = 1
    WHERE TurnoDetalle.IdTurno = ?
    ORDER BY CaraIsla.CodigoCara ASC, MangueraTanque.CodigoManguera ASC
