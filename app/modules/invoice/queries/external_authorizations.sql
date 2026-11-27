DECLARE @Caras XML = ?;
SELECT AE.IdAutorizacion, AE.IdCompania, AE.Informacion, AE.Process, AE.Mensaje,
  AE.FechaEjecucion, AE.FechaInsercion, AE.Autorizado, AE.Cara
FROM dbo.AutorizacionExterna AE WITH (NOLOCK)
WHERE AE.IdCompania = ? AND AE.Cara IN (
  SELECT N.value('.', 'INT') FROM @Caras.nodes('/Ids/Id') T(N))
  AND AE.Process = 0 AND ? IS NOT NULL AND ? IS NOT NULL
ORDER BY AE.FechaInsercion DESC;
