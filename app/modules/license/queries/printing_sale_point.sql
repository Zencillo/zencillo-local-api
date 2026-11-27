SELECT IdCompania, IdCentroVenta, IdPuntoVenta, Documento, Posicion, PosicionFinal
  FROM PuntoVentaImpresion
  WHERE Documento = '1' AND IdPuntoVenta = ?
