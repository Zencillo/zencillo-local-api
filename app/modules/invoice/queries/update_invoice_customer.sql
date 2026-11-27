EXEC dbo.ActualizarDatosFacturaYCliente
 @IdDocumento=?, @Placa=?, @IdentificacionCliente=?, @Kilometraje=?,
 @IdentificacionConductor=?, @NombreCliente=?, @NombreConductor=?, @Correo=?,
 @IdTurno=?, @IdVenta=?, @CodigoIsla=?, @CodigoCultura=?, @IdCompania=?,
 @IdCentroVenta=?, @IdPuntoVenta=?, @IdResolucion=?, @NumeroFactura=?,
 @CodigoComprobante=?, @VentaCredito=?, @IdTransaccion=?,
 @RealizoConsolidacion=?, @ErrorConsolidacion=?;
SELECT CAST(1 AS INT) affectedRows;
