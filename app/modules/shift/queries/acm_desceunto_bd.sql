select 
        sum(valordescuento) as totaldescuento,
        tipo_descuento AS tipo_descuento
    from 
        facturacliente 
    where 
        IdTurno=? and ValorDescuento > 0
    group by tipo_descuento
