IF NOT EXISTS (
    SELECT 1 FROM dbo.ConfiguracionInicial WHERE IdCompania = ? AND IdCentroVenta = ? AND CodigoIsla = ?
)
BEGIN
    RAISERROR ('Estación SQL no autorizada.', 16, 1);
    RETURN;
END;
EXEC dbo.halla_consecutivo_venta @nIsla = ?, @nnumCapturador = ?;
