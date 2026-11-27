SELECT AP.idautorizacionpendiente, AP.identificacioncliente, AP.nombrecliente,
  AP.valorautorizado, AP.tipopreset, AP.formapago, AP.producto, AP.cupoexterno,
  AP.placa, AP.rom, AP.idtransaccion, AP.generanotaentrega, AP.cara, AP.fecha,
  AP.fechaprocesado, AP.pendiente
FROM dbo.autorizacion_pendiente AP WITH (NOLOCK)
WHERE AP.Isla = ? AND AP.pendiente = 1
  AND AP.fecha >= DATEADD(SECOND, -35, GETDATE())
  AND ? IS NOT NULL AND ? IS NOT NULL AND AP.Isla = ?
ORDER BY AP.idautorizacionpendiente DESC;
