SELECT
  FCF.IdFacturaCliente,
  FCF.Acumulado,
  FCF.Redimido,
  FCF.BalanceActual,
  FCF.PuntosActivos,
  FCF.IdentificacionFidelizado,
  FCF.NombreFidelizado,
  FCF.Mensaje,
  FCF.Fecha,
  FCF.ValorRedimido,
  FCF.IdTransaccion,
  FCF.Estado,
  FCF.ValorAcumulado,
  FCF.idtipoidentificacion,
  FCF.TipoPrograma,
  FCF.IdTipoIdentificacionPromocion,
  FCF.NombreClientePromocion,
  FCF.IdentificacionPromocion,
  FCF.IdTipoVehiculo,
  ISNULL(FC.PrefijoFactura, '') AS PrefijoFactura,
  ISNULL(FC.NumeroFactura, '') AS NumeroFactura
FROM FacturaClienteFidelizada FCF WITH(NOLOCK)
INNER JOIN FacturaCliente FC WITH(NOLOCK)
  ON FC.IdFacturaCliente = FCF.IdFacturaCliente
WHERE FCF.TipoPrograma = ?
  AND FC.IdTurno = ?
AND FC.CodigoIsla = CONVERT(VARCHAR(20), ?)
    AND EXISTS (SELECT 1 FROM dbo.ConfiguracionInicial
                WHERE IdCompania = ? AND IdCentroVenta = ? AND CodigoIsla = ?)
ORDER BY FCF.Fecha DESC;