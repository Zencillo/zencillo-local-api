EXEC dbo.sp_CambiarFormaPagoFacturaCompleto
    @IDFacturaCliente = ?, @IDFormaPago = ?, @FormasPago = ?,
    @IdTurno = ?, @CodFp = ?, @Valor = ?,
    @IdDocumento = ?, @IdCompania = ?, @IdCentroVenta = ?, @CodigoCara = ?,
    @IdUltimaVenta = ?, @XMLConsolidador = ?, @XMLFactura = ?,
    @Sincronizada = ?, @CodigoIsla = ?, @IdVenta = ?, @EsUpdate = 1,
    @CodFpOriginal = ?, @ValorReverso = ?, @FormasPagoXml = ?;
