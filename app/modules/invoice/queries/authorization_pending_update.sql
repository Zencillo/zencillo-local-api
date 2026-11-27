UPDATE AP SET pendiente = 0, fechaprocesado = GETDATE()
FROM dbo.autorizacion_pendiente AP
WHERE AP.idautorizacionpendiente = ? AND AP.Isla = ?
  AND ? IS NOT NULL AND ? IS NOT NULL AND AP.Isla = ?;
