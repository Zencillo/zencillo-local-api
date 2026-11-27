IF NOT EXISTS (
    SELECT 1 FROM dbo.ConfiguracionInicial WHERE IdCompania = ? AND IdCentroVenta = ? AND CodigoIsla = ?
)
BEGIN
    RAISERROR ('Estación SQL no autorizada.', 16, 1);
    RETURN;
END;
EXEC dbo.SP_GET_FACTURAS_CLIENTE_COMPLETE
    @MinutosAntes = ?, @IdTipoDocumento = ?, @TopN = ?, @IdFacturaCliente = ?,
    @IdsFacturaCliente = ?, @IdDocumento = ?, @IdTurno = ?, @IdentificacionCliente = ?,
    @TipoVentaExcluido = ?, @CodigoIsla = ?, @NumeroFactura = ?, @SoloConvertidos = ?,
    @FromFormaPago = ?, @NotaCredito = ?, @IsIdDocumento = ?;
