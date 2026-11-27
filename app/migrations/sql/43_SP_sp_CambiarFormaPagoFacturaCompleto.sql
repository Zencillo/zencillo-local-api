-- SQL Server 2008+: orquesta el cambio de forma de pago de una factura.
-- 1) Revierte la forma de pago original en AcumuladoraFormaPago.
-- 2) Aplica las nuevas formas de pago desde XML (sp_ActualizarAcumuladoraFormaPagoBatch).
-- 3) Actualiza FacturaCliente / FormaPagoVenta (actualizarFacturaClienteYFormasPago).
--
-- XML de formas de pago (mismo formato que sp_ActualizarAcumuladoraFormaPagoBatch):
-- <FormasPago>
--   <Item CodFp="01" Valor="1000.0000000" />
-- </FormasPago>

IF OBJECT_ID(N'dbo.sp_CambiarFormaPagoFacturaCompleto', N'P') IS NOT NULL
BEGIN
  DROP PROCEDURE dbo.sp_CambiarFormaPagoFacturaCompleto;
END;

GO

CREATE PROCEDURE dbo.sp_CambiarFormaPagoFacturaCompleto
  @IDFacturaCliente INT,
  @IDFormaPago INT,
  @FormasPago NVARCHAR(MAX),
  @IdTurno INT,
  @CodFp INT,
  @Valor DECIMAL(17, 7),
  @IdDocumento INT,
  @IdCompania INT,
  @IdCentroVenta INT,
  @CodigoCara INT,
  @IdUltimaVenta INT,
  @XMLConsolidador NVARCHAR(MAX),
  @XMLFactura NVARCHAR(MAX),
  @Sincronizada BIT,
  @CodigoIsla INT = 10,
  @IdVenta INT,
  @EsUpdate BIT,
  @CodFpOriginal VARCHAR(50),
  @ValorReverso DECIMAL(17, 7),
  @FormasPagoXml NVARCHAR(MAX)
WITH ENCRYPTION
AS
BEGIN
  SET NOCOUNT ON;

  DECLARE @ErrMsg NVARCHAR(4000);
  DECLARE @ErrNum INT;
  DECLARE @ErrLine INT;

  BEGIN TRY
    IF @CodFpOriginal IS NOT NULL AND LTRIM(RTRIM(@CodFpOriginal)) <> N''
    BEGIN
      EXEC dbo.actualizarAcumuladoraFormaPago
        @IdTurno = @IdTurno,
        @CodFp = @CodFpOriginal,
        @Valor = @ValorReverso;
    END;

    EXEC dbo.sp_ActualizarAcumuladoraFormaPagoBatch
      @IdTurno = @IdTurno,
      @FormasPagoXml = @FormasPagoXml;

    EXEC dbo.actualizarFacturaClienteYFormasPago
      @IDFacturaCliente = @IDFacturaCliente,
      @IDFormaPago = @IDFormaPago,
      @FormasPago = @FormasPago,
      @IdTurno = @IdTurno,
      @CodFp = @CodFp,
      @Valor = @Valor,
      @IdDocumento = @IdDocumento,
      @IdCompania = @IdCompania,
      @IdCentroVenta = @IdCentroVenta,
      @CodigoCara = @CodigoCara,
      @IdUltimaVenta = @IdUltimaVenta,
      @XMLConsolidador = @XMLConsolidador,
      @XMLFactura = @XMLFactura,
      @Sincronizada = @Sincronizada,
      @CodigoIsla = @CodigoIsla,
      @IdVenta = @IdVenta,
      @EsUpdate = @EsUpdate;
  END TRY
  BEGIN CATCH
    SELECT
      @ErrMsg = ERROR_MESSAGE(),
      @ErrNum = ERROR_NUMBER(),
      @ErrLine = ERROR_LINE();

    RAISERROR (
      'sp_CambiarFormaPagoFacturaCompleto | Error %d (Linea %d): %s',
      16,
      1,
      @ErrNum,
      @ErrLine,
      @ErrMsg
    );
  END CATCH;
END;

GO
