SELECT IdHistorialPreset, Cantidad, Hora, Cara, Tipo, IdTurno, Producto
FROM dbo.HistorialPreset WHERE IdTurno = ?;
