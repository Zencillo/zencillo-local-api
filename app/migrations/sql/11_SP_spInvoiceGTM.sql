-- El procedimiento se elimina para permitir recrearlo.
IF OBJECT_ID(N'[dbo].[spInvoiceGTM]', N'P') IS NOT NULL BEGIN DROP
PROCEDURE [dbo].[spInvoiceGTM];

END GO
-- =============================================
-- Author:        WFGD
-- Create date: 7 de noviembre 2023
-- Description:    Proceso para facturacion de guatemala
-- =============================================
CREATE
PROCEDURE spInvoiceGTM @pNumeroFactura VARCHAR(50),
@pPrefijo VARCHAR(50),
@pNumeroAutorizacion VARCHAR(100),
@pIdFacturaCliente INT,
@pIdentificacion VARCHAR(50),
@pNombreCliente VARCHAR(200),
@pIdTurno INT,
@pIdDocumento INT,
@pIsla INT,
@pIdCompania INT,
@IdCVConsolidador INT,
@IdPVCOnsolidador INT
WITH
    ENCRYPTION AS BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
SET
NOCOUNT ON;

DECLARE @ResultadoMensaje VARCHAR(MAX) = '' DECLARE @Resultado INT = 0 BEGIN try BEGIN TRAN
--modifica la factura con los datos
UPDATE FacturaCliente
SET
    Facturada = 1,
    SecuenciaVenta = CONVERT(INT, @pNumeroFactura),
    IdResolucion = NULL,
    PrefijoFactura = @pPrefijo,
    NumeroFactura = @pNumeroFactura,
    IdentificacionCliente = ISNULL(
        @pIdentificacion,
        ISNULL(IdentificacionCliente, '')
    ),
    NombreCliente = ISNULL(@pNombreCliente, ISNULL(NombreCliente, '')),
    CodigoElectronico = @pNumeroAutorizacion
WHERE
    IdFacturaCliente = @pIdFacturaCliente IF NOT EXISTS (
        SELECT
            *
        FROM
            [ModificacionReimpresion]
        WITH
            (NOLOCK)
        WHERE
            IdTurno = @pIdTurno
            AND IdVenta = @pIdDocumento
    ) BEGIN
INSERT INTO
    [dbo].[ModificacionReimpresion] (
        [IdTurno],
        [IdVenta],
        [CodigoIsla],
        [CodigoCultura],
        [IdCompania],
        [IdCentroVenta],
        [IdPuntoVenta],
        [IdResolucion],
        [NumeroFactura],
        [CodigoComprobante],
        [IdentificacionCliente],
        [Cliente],
        [RealizoConsolidacion]
    )
VALUES
    (
        @pIdTurno,
        @pIdDocumento,
        @pIsla,
        502,
        @pIdCompania,
        @IdCVConsolidador,
        @IdPVCOnsolidador,
        NULL,
        @pNumeroFactura,
        NULL,
        @pIdentificacion,
        @pNombreCliente,
        0
    ) END ELSE BEGIN
UPDATE [dbo].[ModificacionReimpresion]
SET
    [CodigoIsla] = @pIsla,
    [CodigoCultura] = 502,
    [IdCompania] = @pIdCompania,
    [IdCentroVenta] = @IdCVConsolidador,
    [IdPuntoVenta] = @IdPVCOnsolidador,
    [IdResolucion] = NULL,
    [NumeroFactura] = @pNumeroFactura,
    [CodigoComprobante] = NULL,
    [IdentificacionCliente] = ISNULL(@pIdentificacion, ''),
    [Cliente] = ISNULL(@pNombreCliente, ''),
    RealizoConsolidacion = 0
WHERE
    IdTurno = @pIdTurno
    AND IdVenta = @pIdDocumento END
SET
    @Resultado = 1
SET
    @ResultadoMensaje = 'Proceso finalizado con exito' COMMIT END try BEGIN catch ROLLBACK
SET
    @Resultado = 0
SET
    @ResultadoMensaje = ERROR_MESSAGE() END catch
SELECT
    @Resultado AS Resultado,
    @ResultadoMensaje AS Mensaje END GO