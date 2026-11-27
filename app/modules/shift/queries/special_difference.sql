SELECT SUM(ISNULL(fcd.Subtotal - (fcd.Cantidad * lec.Precio),0)) AS total
    FROM FacturaCliente as fc with(nolock)
    INNER JOIN MangueraTanque AS Man on Man.CodigoManguera=fc.CodigoManguera
    INNER JOIN TurnoDetalle lec with(nolock) ON Man.IdManguera = lec.IdManguera and lec.IdTurno=fc.IdTurno
    INNER JOIN FacturaClienteDetalle AS fcd on fc.IdFacturaCliente = fcd.IdFacturaCliente
    WHERE fc.IdTurno = ? AND ISNULL(fc.precio_especial, 0) = 1;
