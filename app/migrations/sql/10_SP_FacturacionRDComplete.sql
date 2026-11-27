-- El procedimiento se elimina para permitir recrearlo.
IF OBJECT_ID(N'[dbo].[FacturacionRDComplete]', N'P') IS NOT NULL BEGIN DROP
PROCEDURE [dbo].[FacturacionRDComplete];

END GO
--- =============================================
-- Author:        WILMER GALVIS
-- Create date: 04 ABRIL 2020
-- Description:    PROCESO DE FACTURACION EESPECIFICO PARA RD (OPCION REIMPRESION),
--se comenta idpunto de venta para que solo filtre por idcentroventa
-- add 09 dic 2024 wfgd, se agregan parametros para ingreso de validacion factura electronica (llega ya los datos de la factura)
-- add 27 de abril 2026 wfgd, nuevo parametro para panama @ActualizaResolucion
-- =============================================
CREATE
PROCEDURE [dbo].[FacturacionRDComplete]
-- Add the parameters for the stored procedure here
@IdCompania INT,
@IdCentroVenta INT,
@IdPuntoVenta INT,
@CodComprobante VARCHAR(MAX),
@IdFacturaCliente INT,
@Identificacion VARCHAR(30),
@NombreCliente VARCHAR(200),
@IdCVConsolidador INT,
@IdPVCOnsolidador INT,
--parametros nuevos para setar el numero inicialmente
@IdResolucion INT = 0,
@NumeroFacturaCompleto VARCHAR(MAX) = '',
@PrefijoResolucion VARCHAR(MAX) = '',
@CodigoElectronico VARCHAR(100) = '',
@Descripcion VARCHAR(2000) = '',
@NoValidarResolucion BIT = 0,
@Anulada BIT = 0,
@nFacturada INT = 0,
@ActualizaResolucion BIT = 0
WITH
    ENCRYPTION AS BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
SET
NOCOUNT ON;

DECLARE @UltimoNumeroAsignado INT = 0 DECLARE @NumeroInicial INT = 0 DECLARE @NumeroFinal INT = 0 DECLARE @SecuencialFactura INT = 0,
@NuevoNumeroFactura INT = 0,
@FechaExpiracionResolucion DATE,
@IdTurno INT,
@IdDocumento INT,
@Cultura INT = 809,
@Isla INT
--RESULT
DECLARE @ResultadoMensaje VARCHAR(MAX) = '' DECLARE @Resultado INT = 0 BEGIN TRY
--INICIA TRANSACCION
BEGIN TRAN IF NOT EXISTS (
    SELECT
        IdDocumento
    FROM
        FacturaCliente
    WITH
        (NOLOCK)
    WHERE
        IdFacturaCliente = @IdFacturaCliente
) BEGIN
SET
    @ResultadoMensaje = 'No existe la venta con id: ' + CONVERT(VARCHAR(MAX), @IdFacturaCliente)
SET
    @Resultado = 0 RAISERROR (@ResultadoMensaje, 16, 1) END
    --ASIGNACION DE DATA LOCAL
SELECT
    TOP 1 @IdTurno = IdTurno,
    @IdDocumento = IdDocumento,
    @Isla = CodigoIsla
FROM
    FacturaCliente
WITH
    (NOLOCK)
WHERE
    IdFacturaCliente = @IdFacturaCliente
    --@NoValidarResolucion = 0 indica que es de resolucion no electronica
    IF ISNULL(@NoValidarResolucion, 0) = 0 BEGIN IF EXISTS (
        SELECT
            *
        FROM
            Resolucion
        WITH
            (NOLOCK)
        WHERE
            Resolucion.IdCompania = @IdCompania
            AND Resolucion.CodigoComprobante = @CodComprobante
            AND Resolucion.IdCentroVenta = @IdCentroVenta --AND Resolucion.IdPuntoVenta = @IdPuntoVenta 
            AND Resolucion.EstadoResolucion = 1
    ) BEGIN
SELECT
    @UltimoNumeroAsignado = UltimoNumeroAsignado,
    @NumeroInicial = NumeroInicial,
    @FechaExpiracionResolucion = FechaExpiracionResolucion,
    @NumeroFinal = NumeroFinal,
    @IdResolucion = IdResolucion,
    @PrefijoResolucion = PrefijoFacturacion
FROM
    Resolucion
WHERE
    IdCompania = @IdCompania
    AND CodigoComprobante = @CodComprobante
    AND IdCentroVenta = @IdCentroVenta --AND IdPuntoVenta = @IdPuntoVenta
    AND EstadoResolucion = 1 IF @FechaExpiracionResolucion < CONVERT(DATE, GETDATE()) BEGIN
SET
    @ResultadoMensaje = 'Error : Hay una resolucion activa, pero la fecha de expiracion es menor a la fecha actual.'
SET
    @Resultado = 0 RAISERROR (@ResultadoMensaje, 16, 1) END
SELECT
    TOP 1 @SecuencialFactura = SecuenciaVenta
FROM
    FacturaCliente
WHERE
    IdResolucion = @IdResolucion
ORDER BY
    SecuenciaVenta DESC IF ISNULL(@SecuencialFactura, 0) > ISNULL(@UltimoNumeroAsignado, 0) BEGIN
SET
    @NuevoNumeroFactura = ISNULL(@SecuencialFactura, 0) + 1 END ELSE BEGIN IF ISNULL(@NumeroInicial, 0) > ISNULL(@UltimoNumeroAsignado, 0) BEGIN
SET
    @NuevoNumeroFactura = ISNULL(@NumeroInicial, 1) END ELSE BEGIN
SET
    @NuevoNumeroFactura = ISNULL(@UltimoNumeroAsignado, 0) + 1 END END IF @NuevoNumeroFactura > @NumeroFinal BEGIN
SET
    @ResultadoMensaje = 'Error : Numero Actual ' + CONVERT(VARCHAR(MAX), @NuevoNumeroFactura) + ' Supera al numero final permitido.' + CONVERT(VARCHAR(MAX), @NumeroFinal)
SET
    @Resultado = 0 RAISERROR (@ResultadoMensaje, 16, 1) END ELSE BEGIN
    --modifica la resolucion
UPDATE Resolucion
SET
    UltimoNumeroAsignado = @NuevoNumeroFactura
WHERE
    IdResolucion = @IdResolucion
SET
    @Resultado = 1
SET
    @nFacturada = 1
SET
    @NumeroFacturaCompleto = @PrefijoResolucion + @CodComprobante + RIGHT(
        '00000000' + LTRIM(RTRIM(CONVERT(VARCHAR(MAX), @NuevoNumeroFactura))),
        8
    ) END END ELSE BEGIN
SET
    @ResultadoMensaje = 'Error : No se encontró resolucion activa para este punto de venta'
SET
    @Resultado = 0 RAISERROR (@ResultadoMensaje, 16, 1) END END ELSE BEGIN
SET
    @NuevoNumeroFactura = CONVERT(INT, RIGHT(@NumeroFacturaCompleto, 10)) END
    --modifica la factura con los datos
UPDATE FacturaCliente
SET
    Facturada = @nFacturada,
    SecuenciaVenta = @NuevoNumeroFactura,
    IdResolucion = @IdResolucion,
    PrefijoFactura = @PrefijoResolucion,
    TipoFactura = @CodComprobante,
    NumeroFactura = @NumeroFacturaCompleto,
    IdentificacionCliente = ISNULL(
        @Identificacion,
        ISNULL(IdentificacionCliente, '')
    ),
    NombreCliente = ISNULL(@NombreCliente, ISNULL(NombreCliente, '')),
    Anulada = @Anulada,
    Descripcion = @Descripcion,
    CodigoElectronico = @CodigoElectronico
WHERE
    IdFacturaCliente = @IdFacturaCliente IF @nFacturada = 1 BEGIN IF NOT EXISTS (
        SELECT
            *
        FROM
            [ModificacionReimpresion]
        WITH
            (NOLOCK)
        WHERE
            IdTurno = @IdTurno
            AND IdVenta = @IdDocumento
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
        @IdTurno,
        @IdDocumento,
        @Isla,
        @Cultura,
        @IdCompania,
        @IdCVConsolidador,
        @IdPVCOnsolidador,
        @IdResolucion,
        @NumeroFacturaCompleto,
        @CodComprobante,
        @Identificacion,
        @NombreCliente,
        0
    ) END ELSE BEGIN
UPDATE [dbo].[ModificacionReimpresion]
SET
    [CodigoIsla] = @Isla,
    [CodigoCultura] = @Cultura,
    [IdCompania] = @IdCompania,
    [IdCentroVenta] = @IdCVConsolidador,
    [IdPuntoVenta] = @IdPVCOnsolidador,
    [IdResolucion] = @IdResolucion,
    [NumeroFactura] = @NumeroFacturaCompleto,
    [CodigoComprobante] = @CodComprobante,
    [IdentificacionCliente] = ISNULL(@Identificacion, ''),
    [Cliente] = ISNULL(@NombreCliente, ''),
    RealizoConsolidacion = 0
WHERE
    IdTurno = @IdTurno
    AND IdVenta = @IdDocumento END END IF @ActualizaResolucion = 1 BEGIN
UPDATE Resolucion
SET
    UltimoNumeroAsignado = @NumeroFacturaCompleto
WHERE
    IdResolucion = @IdResolucion END
SET
    @ResultadoMensaje = 'Proceso Finalizado correctamente.'
SET
    @Resultado = 1
    --FINALIZA TRANSACCION
    COMMIT
SELECT
    @Resultado AS Resultado,
    @ResultadoMensaje AS Mensaje,
    @NumeroFacturaCompleto AS NumeroFacturaCompleto,
    @IdResolucion AS IdResolucion END TRY BEGIN CATCH
    --DEVUELVE TRANSACCION
    ROLLBACK
SELECT
    @Resultado AS Resultado,
    ERROR_MESSAGE() AS Mensaje END CATCH END GO