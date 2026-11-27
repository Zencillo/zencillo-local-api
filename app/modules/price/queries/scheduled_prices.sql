SELECT IdArticuloPrecioProgramado, CodigoIsla, IdManguera, CodigoManguera, Precio1, Precio2,
       Precio3, Precio4, Fecha, HoraInicio, HoraFin, Aplicado
FROM ArticuloPrecioProgramado WITH(NOLOCK)
WHERE ArticuloPrecioProgramado.Fecha = ?
AND ArticuloPrecioProgramado.Aplicado = ?
AND ArticuloPrecioProgramado.HoraInicio <= ?
AND ArticuloPrecioProgramado.HoraFin >= ?
AND ArticuloPrecioProgramado.CodigoIsla = ?
