DECLARE @Ids XML = CONVERT(XML, ?);
SELECT TOP (1000) 
      [IdVenta],
      [CodigoCara],
      [IdentificacionCliente],
      [Placa],
      [CodigoArticulo],
      [ValorAutorizado],
      [NombreCliente],
      [Credito],
      [Kilometraje],
      [Estado],
      [CodigoVenta],
      [ValorUnitario],
      [ValorVenta],
      [VolumenVenta],
      [CodigoPOS],
      [CodigoManguera],
      [CodigoIsla],
      [FactorPrecio],
      [CodigoCliente],
      [Calibracion],
      [Fecha],
      [FactorVenta],
      [FactorVolumen],
      [Prepago],
      [IdTurno],
      [IdSecuencial],
      [NumeroCapturador],
      [IdTranControladora],
      [TipoEmision],
      [TipoPreset],
      [FechaAutorizacion],
      [precio_especial]
    FROM Venta
    WHERE CodigoVenta IN (SELECT X.V.value('(text())[1]', 'int') FROM @Ids.nodes('/Ids/Id') AS X(V))
AND CodigoIsla = ?
AND EXISTS (SELECT 1 FROM dbo.ConfiguracionInicial
            WHERE IdCompania = ? AND IdCentroVenta = ? AND CodigoIsla = ?);
