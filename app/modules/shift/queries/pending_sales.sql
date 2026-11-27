SELECT 
      CheckVentasEstacion.IdVentaEstacion AS IdVentaEstacion,    
      CheckVentasEstacion.Cara AS Cara,    
      CheckVentasEstacion.Estado AS Estado,    
      CheckVentasEstacion.IdTurno AS IdTurno,    
      FacturaCliente.IdDocumento AS IdDocumento
    FROM 
      FacturaCliente
      RIGHT OUTER JOIN CheckVentasEstacion
        ON CheckVentasEstacion.IdVentaEstacion = FacturaCliente.IdVentaEstacion
        AND FacturaCliente.IdTurno = CheckVentasEstacion.IdTurno
    INNER JOIN Venta 
        ON CheckVentasEstacion.IdVentaEstacion = Venta.CodigoVenta
		AND VENTA.Estado = 'Finalizada'
    WHERE 
      CheckVentasEstacion.IdTurno = ?
      AND FacturaCliente.IdDocumento IS NULL 
      AND (
        CheckVentasEstacion.aplicaBonoPremio = 0
        OR CheckVentasEstacion.aplicaBonoPremio IS NULL
      )
      AND (
        CheckVentasEstacion.Estado = 0
        OR CheckVentasEstacion.Estado = 1
      )
      AND CheckVentasEstacion.CodigoIsla = ?
    ORDER BY IdVentaEstacion DESC;
