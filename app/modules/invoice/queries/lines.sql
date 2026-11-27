DECLARE @Ids XML = CONVERT(XML, ?), @Company INT = ?, @Center INT = ?, @Island INT = ?;
SELECT 
          FacturaClienteDetalle.IdTipoDocumento AS IdTipoDocumento,    
          FacturaClienteDetalle.IdDocumento AS IdDocumento,    
          FacturaClienteDetalle.IdFacturaClienteDetalle AS IdFacturaClienteDetalle,    
          FacturaClienteDetalle.IdArticulo AS IdArticulo,    
          FacturaClienteDetalle.IdTarifaIVA AS IdTarifaIVA,    
          FacturaClienteDetalle.Cantidad AS Cantidad,    
          FacturaClienteDetalle.ValorUnitario AS ValorUnitario,    
          ISNULL(FacturaClienteDetalle.PorcentajeIVA,0) AS PorcentajeIVA,    
          ISNULL(FacturaClienteDetalle.PorcentajeDescuento,0) AS PorcentajeDescuento,    
          FacturaClienteDetalle.Subtotal AS Subtotal,    
          ISNULL(FacturaClienteDetalle.ValorIVA,0) AS ValorIVA,    
          FacturaClienteDetalle.Total AS Total,    
          FacturaClienteDetalle.ValorDescuento AS ValorDescuento,    
          FacturaClienteDetalle.CodigoICE AS CodigoICE,    
          FacturaClienteDetalle.PorcentajeICE AS PorcentajeICE,    
          FacturaClienteDetalle.ValorICE AS ValorICE,    
          FacturaClienteDetalle.PrecioSinSubsidioECU AS PrecioSinSubsidioECU,    
          Articulo.Presentacion AS Presentacion,    
          FacturaClienteDetalle.FactorSubsidoECU AS FactorSubsidoECU,    
          Articulo.CodigoArticulo AS CodigoArticulo,    
          Articulo.Articulo AS Articulo,    
          Articulo.IncluyeIVA AS IncluyeIVA,    
          Articulo.imprimir_nombre_corto AS ImprimirNombreContro,
          FacturaClienteDetalle.IdFacturaCliente AS IdFacturaCliente,
          ISNULL(Articulo.ImpuestoValorFijo,0) AS ImpuestoValorFijo,
          Articulo.CodigoAlterno,
          Articulo.NombreCorto AS NombreCorto,
          Combustible.IdArticulo AS IdArticuloCombustible
      FROM 
			FacturaClienteDetalle
			LEFT JOIN Articulo ON Articulo.IdArticulo = FacturaClienteDetalle.IdArticulo
			LEFT JOIN Combustible ON Combustible.CodigoArticulo = Articulo.CodigoArticulo
      WHERE 
            FacturaClienteDetalle.IdFacturaCliente IN (
        SELECT X.Item.value('(text())[1]', 'INT') FROM @Ids.nodes('/Ids/Id') AS X(Item)
      ) AND EXISTS (
        SELECT 1 FROM dbo.FacturaCliente AS F
        JOIN dbo.ConfiguracionInicial AS C ON C.CodigoIsla = @Island
        WHERE F.IdFacturaCliente = FacturaClienteDetalle.IdFacturaCliente
          AND F.CodigoIsla = CONVERT(VARCHAR(20), @Island)
          AND C.IdCompania = @Company AND C.IdCentroVenta = @Center
      );
