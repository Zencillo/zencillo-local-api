SELECT 
        CheckVentasEstacion.IdVentaEstacion AS IdVentaEstacion,    
        CheckVentasEstacion.Cara AS Cara,    
        CheckVentasEstacion.Estado AS Estado,    
        CheckVentasEstacion.IdTurno AS IdTurno,    
        FacturaCliente.IdDocumento AS IdDocumento
    FROM 
        FacturaCliente
        RIGHT OUTER JOIN
        CheckVentasEstacion
        ON CheckVentasEstacion.IdVentaEstacion = FacturaCliente.IdVentaEstacion
        AND FacturaCliente.IdTurno = CheckVentasEstacion.IdTurno
    WHERE 
        CheckVentasEstacion.IdTurno = ?
        AND FacturaCliente.IdDocumento IS NULL
        AND (CheckVentasEstacion.Estado = 0 OR CheckVentasEstacion.Estado = 1)
    AND CheckVentasEstacion.CodigoIsla = ?
AND EXISTS (SELECT 1 FROM dbo.ConfiguracionInicial
            WHERE IdCompania = ? AND IdCentroVenta = ? AND CodigoIsla = ?)
ORDER BY IdVentaEstacion DESC;
