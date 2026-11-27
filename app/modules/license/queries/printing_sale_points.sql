SELECT IdCompania, IdCentroVenta, IdPuntoVenta, Documento, Posicion, PosicionFinal
FROM dbo.PuntoVentaImpresion
WHERE Documento = '1' AND IdCompania = ? AND IdCentroVenta = ?;
