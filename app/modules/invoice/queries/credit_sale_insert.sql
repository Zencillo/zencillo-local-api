INSERT INTO dbo.VentasCupo
(IdTransaccion,IdTurno,IdVentaEstacion,Placa,IdentificacionCliente,Estado,Cara,
 ClavePrepago,TipoEnvio,RealizoConsolidacion,Descripcion,TipoAutorizacion,CupoExterno,
 EnvioCupoExterno,ResultadoCupoExterno,Manifiesto,Reintentos,uid,valorautorizado)
VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
SELECT CAST(1 AS INT) affectedRows;
