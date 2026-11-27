INSERT INTO dbo.FormaPagoDetalleAnulado
(IdVenta,IdTurno,IdentificacionRed,CodigoRespuestaActor,MensajeRespuesta,SecuencialTransaccion,NumeroLote,HoraTransaccion,FechaTransaccion,NumeroAutorizacion,TID,MID,ValorInteres,MensajeImpresion,CodigoBanco,NombreBanco,NombreGrupoTarjeta,ModoLectura,NombreTarjetaHabiente,MontoFijo,IdentificadorAplicacion,AID,TipoCrigtograma,PIN,ARQC,NumeroTarjetaTruncado,FechaVencimientoTarjeta,NumeroTarjetaEncriptada,Impuesto,BaseConImpuesto,BaseSinImpuesto,MontoImpuesto,MontoTotal,IdFormaPago,Host,HostName,TipoTarjeta,TipoVenta,NumeroTarjeta,LoteAbierto,NombreTH,Aprobacion,IdTerminal,NumeroReferencia,CodigoReferencia,IdComercio,DiferidoyQuickPayment,Reservado,ArchivoFirma,TVR,TSI,Anulada,Sincronizada)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
SELECT CAST(1 AS INT) affectedRows;

