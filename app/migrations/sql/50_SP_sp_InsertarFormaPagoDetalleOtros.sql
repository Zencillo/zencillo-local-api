-- Inserta un registro en dbo.FormaPagoDetalleOtros (cashback y otros pagos).

IF OBJECT_ID(N'dbo.sp_InsertarFormaPagoDetalleOtros', N'P') IS NOT NULL
BEGIN
  DROP PROCEDURE dbo.sp_InsertarFormaPagoDetalleOtros;
END;

GO

CREATE PROCEDURE dbo.sp_InsertarFormaPagoDetalleOtros
  @IdTurno INT,
  @IdVenta INT = NULL,
  @IdCashBack INT = NULL,
  @IdentificacionRed VARCHAR(10) = NULL,
  @CodigoRespuestaActor VARCHAR(20) = NULL,
  @MensajeRespuesta VARCHAR(2000) = NULL,
  @SecuencialTransaccion INT = NULL,
  @NumeroLote INT = NULL,
  @HoraTransaccion INT = NULL,
  @FechaTransaccion VARCHAR(23) = NULL,
  @NumeroAutorizacion VARCHAR(10) = NULL,
  @TID VARCHAR(20) = NULL,
  @MID VARCHAR(20) = NULL,
  @ValorInteres DECIMAL(18, 7) = NULL,
  @MensajeImpresion VARCHAR(500) = NULL,
  @CodigoBanco INT = NULL,
  @NombreBanco VARCHAR(100) = NULL,
  @NombreGrupoTarjeta VARCHAR(100) = NULL,
  @ModoLectura VARCHAR(6) = NULL,
  @NombreTarjetaHabiente VARCHAR(100) = NULL,
  @MontoFijo VARCHAR(50) = NULL,
  @IdentificadorAplicacion VARCHAR(20) = NULL,
  @AID VARCHAR(20) = NULL,
  @TipoCrigtograma VARCHAR(10) = NULL,
  @PIN VARCHAR(20) = NULL,
  @ARQC VARCHAR(20) = NULL,
  @NumeroTarjetaTruncado VARCHAR(20) = NULL,
  @FechaVencimientoTarjeta INT = NULL,
  @NumeroTarjetaEncriptada VARCHAR(20) = NULL,
  @Impuesto DECIMAL(18, 7) = NULL,
  @BaseConImpuesto DECIMAL(18, 7) = NULL,
  @BaseSinImpuesto DECIMAL(18, 7) = NULL,
  @MontoImpuesto DECIMAL(18, 7) = NULL,
  @MontoTotal DECIMAL(18, 7) = NULL,
  @IdFormaPago INT,
  @Host VARCHAR(10) = NULL,
  @HostName VARCHAR(10) = NULL,
  @TipoTarjeta VARCHAR(10) = NULL,
  @TipoVenta VARCHAR(10) = NULL,
  @NumeroTarjeta VARCHAR(20) = NULL,
  @LoteAbierto VARCHAR(10) = NULL,
  @NombreTH VARCHAR(50) = NULL,
  @Aprobacion VARCHAR(10) = NULL,
  @IdTerminal VARCHAR(10) = NULL,
  @NumeroReferencia VARCHAR(10) = NULL,
  @CodigoReferencia VARCHAR(10) = NULL,
  @IdComercio VARCHAR(20) = NULL,
  @DiferidoyQuickPayment VARCHAR(10) = NULL,
  @Reservado VARCHAR(100) = NULL,
  @ArchivoFirma VARCHAR(100) = NULL,
  @TVR VARCHAR(100) = NULL,
  @TSI VARCHAR(100) = NULL,
  @Anulada BIT = NULL,
  @MultiplesVentas BIT = NULL
WITH ENCRYPTION
AS
BEGIN
  SET NOCOUNT ON;

  DECLARE @ErrMsg NVARCHAR(4000);
  DECLARE @ErrNum INT;
  DECLARE @ErrLine INT;

  BEGIN TRY
    INSERT INTO dbo.FormaPagoDetalleOtros (
      IdTurno,
      IdVenta,
      IdCashBack,
      IdentificacionRed,
      CodigoRespuestaActor,
      MensajeRespuesta,
      SecuencialTransaccion,
      NumeroLote,
      HoraTransaccion,
      FechaTransaccion,
      NumeroAutorizacion,
      TID,
      MID,
      ValorInteres,
      MensajeImpresion,
      CodigoBanco,
      NombreBanco,
      NombreGrupoTarjeta,
      ModoLectura,
      NombreTarjetaHabiente,
      MontoFijo,
      IdentificadorAplicacion,
      AID,
      TipoCrigtograma,
      PIN,
      ARQC,
      NumeroTarjetaTruncado,
      FechaVencimientoTarjeta,
      NumeroTarjetaEncriptada,
      Impuesto,
      BaseConImpuesto,
      BaseSinImpuesto,
      MontoImpuesto,
      MontoTotal,
      IdFormaPago,
      Host,
      HostName,
      TipoTarjeta,
      TipoVenta,
      NumeroTarjeta,
      LoteAbierto,
      NombreTH,
      Aprobacion,
      IdTerminal,
      NumeroReferencia,
      CodigoReferencia,
      IdComercio,
      DiferidoyQuickPayment,
      Reservado,
      ArchivoFirma,
      TVR,
      TSI,
      Anulada,
      MultiplesVentas
    )
    VALUES (
      @IdTurno,
      @IdVenta,
      @IdCashBack,
      @IdentificacionRed,
      @CodigoRespuestaActor,
      @MensajeRespuesta,
      @SecuencialTransaccion,
      @NumeroLote,
      @HoraTransaccion,
      CASE
        WHEN @FechaTransaccion IS NULL OR LTRIM(RTRIM(@FechaTransaccion)) = ''
          THEN NULL
        ELSE CONVERT(DATETIME, @FechaTransaccion, 120)
      END,
      @NumeroAutorizacion,
      @TID,
      @MID,
      @ValorInteres,
      @MensajeImpresion,
      @CodigoBanco,
      @NombreBanco,
      @NombreGrupoTarjeta,
      @ModoLectura,
      @NombreTarjetaHabiente,
      @MontoFijo,
      @IdentificadorAplicacion,
      @AID,
      @TipoCrigtograma,
      @PIN,
      @ARQC,
      @NumeroTarjetaTruncado,
      @FechaVencimientoTarjeta,
      @NumeroTarjetaEncriptada,
      @Impuesto,
      @BaseConImpuesto,
      @BaseSinImpuesto,
      @MontoImpuesto,
      @MontoTotal,
      @IdFormaPago,
      @Host,
      @HostName,
      @TipoTarjeta,
      @TipoVenta,
      @NumeroTarjeta,
      @LoteAbierto,
      @NombreTH,
      @Aprobacion,
      @IdTerminal,
      @NumeroReferencia,
      @CodigoReferencia,
      @IdComercio,
      @DiferidoyQuickPayment,
      @Reservado,
      @ArchivoFirma,
      @TVR,
      @TSI,
      @Anulada,
      @MultiplesVentas
    );
  END TRY
  BEGIN CATCH
    SELECT
      @ErrMsg = ERROR_MESSAGE(),
      @ErrNum = ERROR_NUMBER(),
      @ErrLine = ERROR_LINE();

    RAISERROR (
      'sp_InsertarFormaPagoDetalleOtros | Error %d (Linea %d): %s',
      16,
      1,
      @ErrNum,
      @ErrLine,
      @ErrMsg
    );
  END CATCH;
END;

GO
