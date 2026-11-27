UPDATE dbo.ArticuloPrecioProgramado
SET CodigoIsla = ?, CodigoManguera = ?, Precio1 = ?, Precio2 = ?, Precio3 = ?, Precio4 = ?,
    Fecha = CONVERT(datetime, ?, 120), HoraInicio = ?, HoraFin = ?, Aplicado = ?
WHERE IdArticuloPrecioProgramado = ? AND CodigoIsla = ?
    AND EXISTS (SELECT 1 FROM dbo.ConfiguracionInicial WHERE IdCompania = ? AND IdCentroVenta = ? AND CodigoIsla = ?);
