SELECT 
        AcumuladoraArticulo.IdTurno AS IdTurno,
        AcumuladoraArticulo.CodigoArticulo AS CodigoArticulo,
        AcumuladoraArticulo.Calibracion AS Calibracion,
        AcumuladoraArticulo.CodigoManguera AS CodigoManguera,
        AcumuladoraArticulo.Articulo AS Articulo,
        AcumuladoraArticulo.Cantidad AS Cantidad,
        AcumuladoraArticulo.Valor AS Valor,
        AcumuladoraArticulo.Porcentaje AS Porcentaje,
        AcumuladoraArticulo.ValorUnitario AS ValorUnitario,
        AcumuladoraArticulo.CantidadVentas AS CantidadVentas,
        Articulo.Combustible AS Combustible
      FROM AcumuladoraArticulo WITH(NOLOCK)
      LEFT JOIN Articulo ON Articulo.CodigoArticulo = AcumuladoraArticulo.CodigoArticulo
      WHERE AcumuladoraArticulo.IdTurno = ?  
        
      ORDER BY Porcentaje ASC
