INSERT INTO dbo.gasto_turno (idcompania, idturno, idgastotipo, valor, descripcion, numerofactura, sincronizado)
SELECT ?, ?, ?, ?, ?, ?, ?
WHERE EXISTS (SELECT 1 FROM dbo.TurnoEmpleado WHERE IdTurno = ? AND Isla = ?);
