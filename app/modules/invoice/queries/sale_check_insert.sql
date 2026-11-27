INSERT INTO dbo.CheckVentasEstacion
(IdTurno,IdVentaEstacion,CodigoIsla,Peticion,Cara,Estado,FormaPago,
 FechaProximaRevision,ROM,ClavePrepago,IdentificacionConductor,NombreConductor,
 IdentPasaporte,TotalFleet,GeneraNotaEntrega,VentaCHIPIslero,IdAuthOffline,
 FacturarConductor,BarCodeAutomotor,TipoAuth,IdTransaccionCupo,DatosTransaccion,
 DatosPreciosEDS,idtipovehiculo,clienteQR,manifiesto,generaTicketEfectivoEDS,
 es_credito_contingencia,uid,acumulapuntos)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
SELECT CAST(1 AS INT) affectedRows;
