INSERT INTO dbo.gasto_tipo (
    idgastotipo, idcompania, gastotipo, contabilidadcuenta, estado,
    fechacreacion, fechamodificacion, fechaultimomovimiento
) VALUES (?, ?, ?, ?, ?, CONVERT(datetime, ?, 126), CONVERT(datetime, ?, 126), CONVERT(datetime, ?, 126));
