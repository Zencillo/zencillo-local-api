UPDATE AE SET Process = ?, Mensaje = ?, Autorizado = ?
FROM dbo.AutorizacionExterna AE
WHERE AE.IdAutorizacion = ? AND ? IS NOT NULL AND AE.IdCompania = ?
  AND ? IS NOT NULL AND ? IS NOT NULL;
