DECLARE @Ids XML = CONVERT(XML, ?);
SELECT FCF.IdFacturaCliente, FCF.Acumulado, FCF.Redimido, FCF.BalanceActual, FCF.PuntosActivos, FCF.IdentificacionFidelizado, FCF.NombreFidelizado, FCF.Mensaje, FCF.Fecha, FCF.ValorRedimido, FCF.IdTransaccion, FCF.Estado, FCF.ValorAcumulado, FCF.idtipoidentificacion, FCF.TipoPrograma, FCF.IdTipoIdentificacionPromocion, FCF.NombreClientePromocion, FCF.IdentificacionPromocion, FCF.IdTipoVehiculo
FROM dbo.FacturaClienteFidelizada AS FCF WITH (NOLOCK)
JOIN dbo.FacturaCliente AS FC ON FC.IdFacturaCliente = FCF.IdFacturaCliente
WHERE FCF.IdFacturaCliente IN (
    SELECT X.V.value('(text())[1]', 'int') FROM @Ids.nodes('/Ids/Id') AS X(V)
)
AND (
    ISNULL(FCF.IdTipoIdentificacionPromocion, 0) <> 0
    OR ISNULL(LTRIM(RTRIM(FCF.NombreClientePromocion)), '') <> ''
    OR ISNULL(LTRIM(RTRIM(FCF.IdentificacionPromocion)), '') <> ''
    OR ISNULL(FCF.IdTipoVehiculo, 0) <> 0
)
AND FC.CodigoIsla = CONVERT(VARCHAR(20), ?)
    AND EXISTS (SELECT 1 FROM dbo.ConfiguracionInicial
                WHERE IdCompania = ? AND IdCentroVenta = ? AND CodigoIsla = ?);
