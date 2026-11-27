-- El procedimiento se elimina para permitir recrearlo.
IF OBJECT_ID(N'[dbo].[InvoiceFastConversion]', N'P') IS NOT NULL BEGIN DROP
PROCEDURE [dbo].[InvoiceFastConversion];

END GO
--===========================================
-- Author:        WILMER GALVIS
-- Create date: HACE MUCHO NO ME ACUERDO COMO EN EL 2020 AGOSTO
-- Description:    SP ENCARGADO DE CREAR LA FACTURA ELECTRONICA EN BASE A UNA FACTURA POS.
-- ADD 31 DE JUL 2027 WFGD, SE VALIDA QUE NO  EXISTA EL LA TANLA EL IDFACTURACLIENTE
-- =============================================
CREATE
PROCEDURE [dbo].[InvoiceFastConversion] @IdCompania INT,
@IdCentroVenta INT,
@IdPuntoVenta INT,
@IdFacturaCliente INT,
@IdentificacionCliente VARCHAR(50),
@NombreCliente VARCHAR(200),
@Placa VARCHAR(20),
@TipoVenta INT,
@CodComprobante VARCHAR(10),
@Kilometraje VARCHAR(15),
@Isla INT
WITH
    ENCRYPTION AS BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
SET
NOCOUNT ON;

DECLARE @nSecuenciaVenta INT = 0 DECLARE @SecuencialIdVenta INT = 0 DECLARE @SecuencialIdDocumento INT = 0 DECLARE @CodArea INT = 0 DECLARE @SecuencialFactura INT = 0 DECLARE @SecuencialFacturaConversion INT = 0 DECLARE @SecuencialActualFactura INT = 0 DECLARE @NitCompania VARCHAR(MAX) DECLARE @NuevoNumeroFactura INT = 0 DECLARE @UltimoNumeroAsignado INT DECLARE @NumeroInicial INT DECLARE @NumeroFinal INT DECLARE @ResultadoMensaje VARCHAR(MAX) = '' DECLARE @Resultado INT = 0 DECLARE @IdResolucion INT = 0 DECLARE @PrefijoResolucion VARCHAR(MAX) = '' DECLARE @nFacturada INT = 0 DECLARE @ClaveTecnicaResolucion VARCHAR(MAX) DECLARE @FechaExpiracionResolucion DATE DECLARE @NumeroFacturaCompleto VARCHAR(MAX) BEGIN TRY BEGIN TRANSACTION IF EXISTS (
    SELECT
        TOP 1 1
    FROM
        FacturaClienteConversion
    WITH
        (nolock)
    WHERE
        IdFacturaCliente = @IdFacturaCliente
) BEGIN RAISERROR (
    'La venta enviada ya fue Convertida anteriormente, solo se puede convertir una sola vez.',
    16,
    1
) END
SELECT
    @IdCompania = IdCompania,
    @SecuencialIdVenta = SecuencialIdVenta,
    @NitCompania = Nitcompania,
    @CodArea = Codigoarea,
    @SecuencialActualFactura = SecuenciaActualFactura
FROM
    ConfiguracionInicial
WHERE
    CodigoIsla = @Isla
SELECT
    TOP 1 @SecuencialIdDocumento = FacturaCliente.IdDocumento
FROM
    FacturaCliente
WHERE
    FacturaCliente.CodigoIsla = @Isla
ORDER BY
    IdDocumento DESC
    --NUMERO DE ID DOCUMENTO
    IF ISNULL(@SecuencialIdDocumento, 0) > ISNULL(@SecuencialIdVenta, 0) BEGIN
SET
    @SecuencialIdVenta = ISNULL(@SecuencialIdDocumento, 0) + 1 END ELSE BEGIN
SET
    @SecuencialIdVenta = ISNULL(@SecuencialIdVenta, 0) + 1 END
    /**************************************************************/
    --BUSCA RESOLUCION DE FACTURACION
    IF EXISTS (
        SELECT
            *
        FROM
            Resolucion
        WITH
            (NOLOCK)
        WHERE
            Resolucion.IdCompania = @IdCompania
            AND Resolucion.IdCentroVenta = @IdCentroVenta
            AND Resolucion.IdPuntoVenta = @IdPuntoVenta
            AND Resolucion.EstadoResolucion = 1
            AND Resolucion.CodigoComprobante = CASE
                WHEN @CodArea = 57 THEN @CodComprobante
                ELSE Resolucion.CodigoComprobante
            END
    ) BEGIN
SELECT
    TOP 1 @FechaExpiracionResolucion = FechaExpiracionResolucion,
    @ClaveTecnicaResolucion = ClaveTecnica,
    @IdResolucion = IdResolucion,
    @UltimoNumeroAsignado = UltimoNumeroAsignado,
    @NumeroInicial = NumeroInicial,
    @NumeroFinal = NumeroFinal,
    @PrefijoResolucion = ISNULL(PrefijoFacturacion, '')
FROM
    Resolucion
WHERE
    Resolucion.IdCompania = @IdCompania
    AND Resolucion.IdCentroVenta = @IdCentroVenta
    AND Resolucion.IdPuntoVenta = @IdPuntoVenta
    AND Resolucion.EstadoResolucion = 1
    AND Resolucion.CodigoComprobante = CASE
        WHEN @CodArea = 57 THEN @CodComprobante
        ELSE Resolucion.CodigoComprobante
    END IF @FechaExpiracionResolucion >= SYSDATETIME() BEGIN
SELECT
    TOP 1 @SecuencialFactura = SecuenciaVenta
FROM
    FacturaCliente
WHERE
    FacturaCliente.IdResolucion = @IdResolucion
    AND FacturaCliente.SecuenciaVenta <> 0
ORDER BY
    SecuenciaVenta DESC
    --QRY NECESARIO PARA NO PERDER CONSECUTIVOS DE FACTURAS    
SELECT
    TOP 1 @SecuencialFacturaConversion = FacturaClienteConversion.SecuenciaVenta
FROM
    FacturaClienteConversion
WHERE
    FacturaClienteConversion.IdResolucion = @IdResolucion
    AND FacturaClienteConversion.SecuenciaVenta <> 0
ORDER BY
    FacturaClienteConversion.SecuenciaVenta DESC IF ISNULL(@SecuencialFactura, 0) < ISNULL(@SecuencialFacturaConversion, 0) BEGIN
SET
    @SecuencialFactura = @SecuencialFacturaConversion END IF ISNULL(@SecuencialFactura, 0) > ISNULL(@UltimoNumeroAsignado, 0) BEGIN
SET
    @NuevoNumeroFactura = @SecuencialFactura END ELSE BEGIN IF ISNULL(@UltimoNumeroAsignado, 0) = 0 BEGIN
SET
    @NuevoNumeroFactura = ISNULL(@NumeroInicial, 1) - 1 END ELSE BEGIN
SET
    @NuevoNumeroFactura = ISNULL(@UltimoNumeroAsignado, 0) END END
SET
    @NuevoNumeroFactura = @NuevoNumeroFactura + 1 IF @NuevoNumeroFactura <= @NumeroFinal BEGIN DECLARE @EstadoResolucion INT = 0 IF @UltimoNumeroAsignado >= @NumeroFinal BEGIN
UPDATE Resolucion
SET
    EstadoResolucion = 0
WHERE
    IdResolucion = @IdResolucion END
SET
    @NumeroFacturaCompleto = CONVERT(VARCHAR(MAX), @NuevoNumeroFactura)
UPDATE Resolucion
SET
    UltimoNumeroAsignado = @NuevoNumeroFactura
WHERE
    IdResolucion = @IdResolucion
SET
    @Resultado = 1
SET
    @nFacturada = 1 END ELSE BEGIN
SET
    @ResultadoMensaje = 'Error : El número final calculado supera el número final permitido: Numero Calculado: ' + CONVERT(VARCHAR(MAX), @NuevoNumeroFactura) + ' Numero Final Resolucion: ' + CONVERT(VARCHAR(MAX), @NumeroFinal)
SET
    @Resultado = 0 RAISERROR (@ResultadoMensaje, 16, 1) END END ELSE BEGIN
SET
    @ResultadoMensaje = 'Error : Hay una resolucion activa, pero la fecha de expiracion es menor a la fecha actual.'
SET
    @Resultado = 0 RAISERROR (@ResultadoMensaje, 16, 1) END END ELSE BEGIN
SET
    @ResultadoMensaje = 'Error : No se encontró resolucion activa para este punto de venta'
SET
    @Resultado = 0 RAISERROR (@ResultadoMensaje, 16, 1) END IF @Resultado = 0 BEGIN ROLLBACK
SELECT
    @Resultado AS Resultado,
    @ResultadoMensaje AS Mensaje RETURN END
SET
    @nSecuenciaVenta = @NuevoNumeroFactura
    --ASIGNA NULL'S EN CASO DE VACIO O CERO
    IF @IdResolucion = 0 BEGIN
SET
    @IdResolucion = NULL END IF @PrefijoResolucion = '' BEGIN
SET
    @PrefijoResolucion = NULL END
INSERT INTO
    [dbo].[FacturaClienteConversion] (
        [IdFacturaCliente],
        [IdDocumento],
        [Fecha],
        [IdResolucion],
        [PrefijoFactura],
        [IdentificacionCliente],
        [NombreCliente],
        [NumeroFactura],
        [Placa],
        [SecuenciaVenta],
        [TipoFactura],
        [CodigoElectronico],
        [Kilometraje],
        [TipoVenta]
    )
VALUES
    (
        @IdFacturaCliente,
        @SecuencialIdVenta,
        SYSDATETIME(),
        @IdResolucion,
        @PrefijoResolucion,
        @IdentificacionCliente,
        @NombreCliente,
        @NumeroFacturaCompleto,
        @Placa,
        @nSecuenciaVenta,
        @CodComprobante,
        '',
        @Kilometraje,
        @TipoVenta
    ) DECLARE @IdFacturaClienteConversion INT = @@IDENTITY --obtiene el idfacturaclienteconversion creado    
    --MODIFICA EL SECUENCUAL IDVENTA IDDOCUMENTO GENERADO
UPDATE ConfiguracionInicial
SET
    SecuenciaActualFactura = @NuevoNumeroFactura,
    SecuencialIdVenta = @SecuencialIdVenta
WHERE
    CodigoIsla = @Isla
    --validacion fp original
    DECLARE @IdFpVenta INT = 0
SELECT
    @IdFpVenta = IdFormaPago
FROM
    FacturaCliente
WITH
    (NOLOCK)
WHERE
    IdFacturaCliente = @IdFacturaCliente
    --si la venta es credito directo o prepago, entonces se toma como referencia la tabla ControlProcesosPorVentaCupo
    IF @IdFpVenta = 6
    OR @IdFpVenta = 97 BEGIN
    --INSERTA DATOS DE PROCESAMIENTOS DE VENTA.
INSERT INTO
    [dbo].[ControlProcesosPorVenta] (
        [IdTurno],
        [IdVenta],
        [TipoVenta],
        [FechaZeta],
        [HoraTurno],
        [CambioFormaPagoVenta],
        [Isla],
        [NumeroCara],
        [IdCentroVenta],
        [NumeroDeTurno],
        [IdentificacionEmpleado],
        [RealizoFidelizacion],
        [CodigoErrorFidelizacion],
        [ErrorFidelizacion],
        [RealizoConsolidacion],
        [CodigoErrorConsolidacion],
        [ErrorConsolidacion],
        [CodigoErrorFormasPagoConsolidacion],
        [ErrorFormasPagoConsolidacion],
        [XMLFacturacion],
        [XMLFidelizacion],
        [XMLConsolidacion],
        [UsuarioLicenciamiento],
        [PasswordLicenciamiento],
        [IMEILicenciamiento],
        [SincronizoFormasPagoFacturacion],
        [RealizoFacturacion],
        [CodigoErrorFacturacion],
        [ErrorFacturacion],
        [FechaVenta],
        [FormaPagoProcesada],
        [HoraVenta],
        [IdPuntoVenta],
        [SincronizaFormasPagoConsolidacion],
        [SincronizaSICOM],
        [SincronizaSYSCOM]
    )
SELECT
    FC.IdTurno,
    @SecuencialIdVenta,
    @TipoVenta,
    CPPV.FechaZeta,
    CPPV.HoraTurno,
    0,
    CPPV.Isla,
    CPPV.NumeroCara,
    CPPV.IdCentroVenta,
    CPPV.NumeroDeTurno,
    CPPV.IdentificacionEmpleado,
    0,
    '',
    '',
    0,
    '',
    '',
    '',
    '',
    '',
    '',
    '',
    CPPV.UsuarioLicenciamiento,
    CPPV.[PasswordLicenciamiento],
    CPPV.[IMEILicenciamiento],
    0,
    0,
    '',
    '',
    CPPV.[FechaVenta],
    0,
    CPPV.[HoraVenta],
    CPPV.[IdPuntoVenta],
    0,
    2,
    2
FROM
    ControlProcesosPorVentaCupo AS CPPV
WITH
    (NOLOCK)
    INNER JOIN FacturaCliente AS FC
WITH
    (NOLOCK) ON (
        CONVERT(VARCHAR(MAX), CPPV.Isla) + CONVERT(VARCHAR(MAX), FC.IdDocumento) = CPPV.IdVenta
        AND FC.CodigoIsla = CPPV.Isla
    )
WHERE
    FC.IdFacturaCliente = @IdFacturaCliente END ELSE BEGIN
    --INSERTA DATOS DE PROCESAMIENTOS DE VENTA.
INSERT INTO
    [dbo].[ControlProcesosPorVenta] (
        [IdTurno],
        [IdVenta],
        [TipoVenta],
        [FechaZeta],
        [HoraTurno],
        [CambioFormaPagoVenta],
        [Isla],
        [NumeroCara],
        [IdCentroVenta],
        [NumeroDeTurno],
        [IdentificacionEmpleado],
        [RealizoFidelizacion],
        [CodigoErrorFidelizacion],
        [ErrorFidelizacion],
        [RealizoConsolidacion],
        [CodigoErrorConsolidacion],
        [ErrorConsolidacion],
        [CodigoErrorFormasPagoConsolidacion],
        [ErrorFormasPagoConsolidacion],
        [XMLFacturacion],
        [XMLFidelizacion],
        [XMLConsolidacion],
        [UsuarioLicenciamiento],
        [PasswordLicenciamiento],
        [IMEILicenciamiento],
        [SincronizoFormasPagoFacturacion],
        [RealizoFacturacion],
        [CodigoErrorFacturacion],
        [ErrorFacturacion],
        [FechaVenta],
        [FormaPagoProcesada],
        [HoraVenta],
        [IdPuntoVenta],
        [SincronizaFormasPagoConsolidacion],
        [SincronizaSICOM],
        [SincronizaSYSCOM]
    )
SELECT
    CPPV.IdTurno,
    @SecuencialIdVenta,
    @TipoVenta,
    CPPV.FechaZeta,
    CPPV.HoraTurno,
    0,
    CPPV.Isla,
    CPPV.NumeroCara,
    CPPV.IdCentroVenta,
    CPPV.NumeroDeTurno,
    CPPV.IdentificacionEmpleado,
    0,
    '',
    '',
    0,
    '',
    '',
    '',
    '',
    '',
    '',
    '',
    CPPV.UsuarioLicenciamiento,
    CPPV.[PasswordLicenciamiento],
    CPPV.[IMEILicenciamiento],
    0,
    0,
    '',
    '',
    CPPV.[FechaVenta],
    0,
    CPPV.[HoraVenta],
    CPPV.[IdPuntoVenta],
    0,
    2,
    2
FROM
    ControlProcesosPorVenta AS CPPV
WITH
    (NOLOCK)
    INNER JOIN FacturaCliente AS FC
WITH
    (NOLOCK) ON (
        FC.IdDocumento = CPPV.IdVenta
        AND FC.CodigoIsla = CPPV.Isla
    )
WHERE
    FC.IdFacturaCliente = @IdFacturaCliente END IF NOT EXISTS (
        SELECT
            *
        FROM
            ControlProcesosPorVenta
        WITH
            (NOLOCK)
        WHERE
            Isla = @Isla
            AND IdVenta = @SecuencialIdVenta
            AND TipoVenta = @TipoVenta
    ) BEGIN
SET
    @ResultadoMensaje = 'Error : No se logró crear el registro completo en controlprocesoporventa'
SET
    @Resultado = 0 RAISERROR (@ResultadoMensaje, 16, 1) END
UPDATE FacturaCliente
SET
    VentaConvertida = 1,
    Anulada = 1
WHERE
    IdFacturaCliente = @IdFacturaCliente COMMIT
    --RESULTADO
SELECT
    @Resultado AS Resultado,
    @ResultadoMensaje AS Mensaje,
    @NuevoNumeroFactura AS NUMFACURA,
    @IdResolucion AS IDRESOLUCION,
    @SecuencialIdVenta AS IDDOC,
    @IdFacturaClienteConversion AS IdFacturaCliente,
    @PrefijoResolucion AS PrefijoFactura,
    @ClaveTecnicaResolucion AS ClaveTecnicaResolucion END TRY BEGIN CATCH ROLLBACK
    --RESULTADO
SELECT
    0 AS Resultado,
    ERROR_MESSAGE() AS Mensaje END CATCH END GO