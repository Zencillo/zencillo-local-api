SELECT AP.IdArticuloPrecioProgramadoManual, AP.IdentificacionEmpleado, AP.CodigoIsla, AP.IdManguera, AP.CodigoManguera, AP.Precio, AP.FechaEnviado, AP.Aplicado, C.Nombre
    FROM ArticuloPrecioProgramadoManual AS AP
    INNER JOIN MangueraTanque AS MT ON MT.IdManguera = AP.IdManguera
    INNER JOIN Combustible AS C ON C.IdCombustible = MT.IdCombustible
    WHERE AP.CodigoIsla = ?
