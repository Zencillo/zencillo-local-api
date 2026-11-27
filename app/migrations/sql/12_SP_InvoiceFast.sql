-- =============================================
-- Author:		wilmer fabian galvis duarte
-- Create date: 2022-12-16
-- Description:	sp encargado de crear la factura de canastilla mobile y recuperacion de ventas, ADD 08 NOV 2023 PARAMETROS DE NUM FAC PARA CULTURA 502 GTM
-- add 18 sep 2024 validacion que la venta no existe en facturacliente solo si llega idventaestacion  > 0
-- add 22 oct 2024, vaidacion si debe o no facturar ventas de consumidor final
-- ADD 12 OCT 2024 WFGD, ADD Variables de control para RD factura electronica  (no validar resolucion)
-- ADD 17 DIC 2024, SI YA EXISTE LA VENTA DEVUELVE 1 EN EL RESULTADO
-- ADD 30 DE MAYO 2-25 WFGD AJUSTES PARA FAC ELECTRONICA RD
-- Author:		andy paul guzman escalera
-- ADD 21 DE JULIO 2026 AJUSTE PARA QUE LA ACUMULADORA QUEDE CORRECTAMENTE
-- ADD 21 OCT 2026 traza InvoiceFastLog (variable tabla, volcado post COMMIT/ROLLBACK)
-- ADD 21 OCT 2026 mas detalle en Detalle (ids, montos, manguera, nodos XML)
-- =============================================
IF OBJECT_ID(N'dbo.InvoiceFastLog', N'U') IS NULL BEGIN
CREATE TABLE
    dbo.InvoiceFastLog (
        Id INT IDENTITY(1, 1) NOT NULL,
        Fecha DATETIME NOT NULL,
        Paso VARCHAR(80) NOT NULL,
        Accion VARCHAR(40) NOT NULL,
        IdTurno INT NULL,
        IdVentaEstacion INT NULL,
        nCanastilla INT NULL,
        IdFacturaCliente INT NULL,
        CodigoArticulo VARCHAR(80) NULL,
        CodigoManguera INT NULL,
        Detalle VARCHAR(1000) NULL,
        CONSTRAINT PK_InvoiceFastLog PRIMARY KEY CLUSTERED (Id ASC)
    );

CREATE NONCLUSTERED INDEX IX_InvoiceFastLog_Fecha ON dbo.InvoiceFastLog (Fecha DESC);

CREATE NONCLUSTERED INDEX IX_InvoiceFastLog_IdVentaEstacion ON dbo.InvoiceFastLog (IdVentaEstacion);

END
GO
CREATE
PROCEDURE [dbo].[InvoiceFast] @Isla INT,
@IdCompania INT,
@IdCentroVenta INT,
@IdPuntoVenta INT,
@CodComprobante VARCHAR(MAX),
@nCalibracion INT,
@bGeneraNotaEntrega INT,
@nCodFp INT,
@bCreditoFactura INT,
@nCanastilla INT,
@nIdTurno INT,
@nIdTipoDocumento INT,
@nCodigoIsla INT,
@sFechaFormateada VARCHAR(MAX),
@nHoraEntrega INT,
@sIdentificacionCliente VARCHAR(MAX),
@sNombreCliente VARCHAR(MAX),
@sFormasPago VARCHAR(MAX),
@sPlaca VARCHAR(MAX),
@sKilometraje VARCHAR(MAX),
@rTotalIVAS DECIMAL(17, 7),
@rSubtotal DECIMAL(17, 7),
@rValorTotalFactura DECIMAL(17, 7),
@rPorcentajeDescuento DECIMAL(17, 7),
@rValorDescuento DECIMAL(17, 7),
@rPropina DECIMAL(17, 7),
@rTotalICE DECIMAL(17, 7),
@rValorTotalSinSubsidioECU DECIMAL(17, 7),
@rAhorroPorSubsidioECU DECIMAL(17, 7),
@rRecaudoSUIC DECIMAL(17, 7),
@rTotalaPagar DECIMAL(17, 7),
@nCodigoCara INT,
@nCodigoManguera INT,
@nIdVentaEstacion INT,
@rPuntosAcumulados DECIMAL(17, 7),
@nFechaProximaRevicion INT,
@nTipoVenta INT,
@nTipoFactura INT,
@nTipoEmision INT,
@sIdentificacionConductor VARCHAR(MAX),
@sNombreConductor VARCHAR(MAX),
@nIdentPasaporte INT,
@nTotalFleet INT,
@sROM VARCHAR(MAX),
@nVentaCHIPIslero INT,
@nFacturarConductor INT,
@sBarCodeAutomotor VARCHAR(MAX),
@sTipoAuth VARCHAR(MAX),
@TotalImpuestoFijo DECIMAL(17, 7),
@ModeSale INT,
@TipoDescuento INT = 0,
-----valores de detalle
@IdArticuloDet INT,
@IdTarifaIVADet INT,
@CantidadDet DECIMAL(18, 7),
@ValorUnitarioDet DECIMAL(18, 7),
@PorcentajeIVADet INT,
@PorcentajeDescuentoDet INT,
@SubtotalDet DECIMAL(18, 7),
@ValorIVADet DECIMAL(18, 7),
@TotalDet DECIMAL(18, 7),
@ValorDescuentoDet DECIMAL(18, 7),
@CodigoICEDet VARCHAR(10),
@PorcentajeICEDet INT,
@ValorICEDet DECIMAL(18, 7),
@FactorSubsidoECUDet DECIMAL(18, 7),
@PrecioSinSubsidioECUDet DECIMAL(18, 7),
@TipoIVADet INT,
--datos para procesamiento de la venta.
@nCupo INT,
@nHoraTurnoActivo INT,
@nFechaZActiva INT,
@nSincronizaSICOM INT,
@nSincronizaSYSCOM INT,
@nNumeroTurno INT,
@nIdCentroVentaCons INT,
@nIdPuntoVentaCons INT,
@nIdentificacionEmpelado INT,
@sUsuarioFacturacion VARCHAR(MAX),
@sPassFacturacion VARCHAR(MAX),
@sIMEI VARCHAR(MAX),
@nFechaVenta INT,
@nHoraVenta INT,
--Recaudo 
@nRecaudo INT,
--detalles de canastilla
@sXMLDetCanastilla VARCHAR(MAX),
--factura ya con datos seteados ej guatemala y rd electronica
@pNumeroFactura VARCHAR(50) = NULL,
@pPrefijo VARCHAR(10) = NULL,
@pCodigoElectronico VARCHAR(100) = NULL,
@pNoValidarResolucion BIT = 0,
@pIdResolucion INT = 0,
@pAnulada BIT = 0,
@pDescripcion VARCHAR(1000) = ''
WITH
    ENCRYPTION AS BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
SET
NOCOUNT ON;

DECLARE @nSecuenciaVenta INT = 0 DECLARE @SecuencialIdVenta INT = 0 DECLARE @SecuencialIdDocumento INT = 0 DECLARE @CodArea INT = 0 DECLARE @SecuencialFactura INT = 0 DECLARE @SecuencialFacturaConversion INT = 0 DECLARE @SecuencialActualFactura INT = 0 DECLARE @NitCompania VARCHAR(MAX) DECLARE @NuevoNumeroFactura INT = 0 DECLARE @UltimoNumeroAsignado INT DECLARE @NumeroInicial INT DECLARE @NumeroFinal INT DECLARE @ResultadoMensaje VARCHAR(MAX) = '' DECLARE @Resultado INT = 0 DECLARE @IdResolucion INT = 0 DECLARE @PrefijoResolucion VARCHAR(MAX) = '' DECLARE @nFacturada INT = 0 DECLARE @ClaveTecnicaResolucion VARCHAR(MAX) DECLARE @FechaExpiracionResolucion DATE DECLARE @NumeroFacturaCompleto VARCHAR(MAX) DECLARE @IdFacturaCliente INT = 0
--VARIABLE QUE INDICA SI DEBE FACTURAR O NO TODO.
DECLARE @FacturarSiempre INT = 0,
--PARA COL SI SE DEBE VALIDAR O NO EL UVT
@COLValidarUVT INT = 0,
--VALOR BASE PARA VALIDAR EL UVT
@COLValorUVT DECIMAL(17, 7) = 0,
@PANGenerarArchivo BIT = 0,
@IdTipoVehiculo INT = 0,
@NoFacturarAuthAConsumidorFinal INT = 0
DECLARE @CodArt VARCHAR(MAX)
DECLARE @Articulo VARCHAR(MAX)
DECLARE @Log TABLE (
    Paso VARCHAR(80) NOT NULL,
    Accion VARCHAR(40) NOT NULL,
    CodigoArticulo VARCHAR(80) NULL,
    CodigoManguera INT NULL,
    Detalle VARCHAR(1000) NULL
)
DECLARE @InvoiceFastLogError VARCHAR(1000) = ''
--OBTIENE LO QUE ESTA EN BASE DE DATOS CON LLAVE FACTURAR_TODAS_LAS_VENTAS
SELECT
    TOP 1 @FacturarSiempre = CONVERT(INT, Valor)
FROM
    ConfiguracionCapturador
WITH
    (NOLOCK)
WHERE
    Llave = 'FACTURAR_TODAS_LAS_VENTAS'
SELECT
    TOP 1 @COLValidarUVT = CONVERT(INT, Valor)
FROM
    ConfiguracionCapturador
WITH
    (NOLOCK)
WHERE
    Llave = 'COL_VALIDA_UVT'
SELECT
    TOP 1 @COLValorUVT = CONVERT(DECIMAL, Valor)
FROM
    ConfiguracionCapturador
WITH
    (NOLOCK)
WHERE
    Llave = 'COL_VALIDA_UVT_VALOR'
SELECT
    TOP 1 @NoFacturarAuthAConsumidorFinal = CONVERT(INT, Valor)
FROM
    ConfiguracionCapturador
WITH
    (NOLOCK)
WHERE
    Llave = 'EDS_NO_FACTURAR_AUTOMATICAMENTE_VENTAS_CONSUMIDOR_FINAL'
SELECT
    TOP 1 @PANGenerarArchivo = ISNULL(GeneraArchivoVentaPanama, 0)
FROM
    ConfiguracionInicial
WITH
    (NOLOCK)
WHERE
    CodigoIsla = @Isla
    --TIPO DE VEHICULO
SELECT
    TOP 1 @IdTipoVehiculo = idtipovehiculo
FROM
    CheckVentasEstacion
WITH
    (NOLOCK)
WHERE
    IdVentaEstacion = @nIdVentaEstacion
    AND IdTurno = @nIdTurno BEGIN TRY
INSERT INTO @Log (Paso, Accion, Detalle)
VALUES (
    'INICIO',
    'START',
    LEFT(
        'isla=' + CONVERT(VARCHAR(12), ISNULL(@Isla, 0))
        + ' nCanastilla=' + CONVERT(VARCHAR(12), ISNULL(@nCanastilla, 0))
        + ' nIdVentaEstacion=' + CONVERT(VARCHAR(12), ISNULL(@nIdVentaEstacion, 0))
        + ' nIdTurno=' + CONVERT(VARCHAR(12), ISNULL(@nIdTurno, 0))
        + ' nTipoVenta=' + CONVERT(VARCHAR(12), ISNULL(@nTipoVenta, 0))
        + ' ModeSale=' + CONVERT(VARCHAR(12), ISNULL(@ModeSale, 0))
        + ' nCodFp=' + CONVERT(VARCHAR(12), ISNULL(@nCodFp, 0))
        + ' fp=' + LEFT(ISNULL(@sFormasPago, ''), 30)
        + ' cara=' + CONVERT(VARCHAR(12), ISNULL(@nCodigoCara, 0))
        + ' manguera=' + CONVERT(VARCHAR(12), ISNULL(@nCodigoManguera, 0))
        + ' calib=' + CONVERT(VARCHAR(12), ISNULL(@nCalibracion, 0))
        + ' cupo=' + CONVERT(VARCHAR(12), ISNULL(@nCupo, 0))
        + ' notaEntrega=' + CONVERT(VARCHAR(12), ISNULL(@bGeneraNotaEntrega, 0))
        + ' creditoFac=' + CONVERT(VARCHAR(12), ISNULL(@bCreditoFactura, 0))
        + ' total=' + CONVERT(VARCHAR(24), ISNULL(@rTotalaPagar, 0))
        + ' sub=' + CONVERT(VARCHAR(24), ISNULL(@rSubtotal, 0))
        + ' xmlLen=' + CONVERT(VARCHAR(12), ISNULL(LEN(@sXMLDetCanastilla), 0))
        + ' comp=' + LEFT(ISNULL(@CodComprobante, ''), 12)
        + ' tipoAuth=' + LEFT(ISNULL(@sTipoAuth, ''), 20),
        1000
    )
)
    --SE VERIFICA QUE YA LA VENTA NO EXISTA EN FACTURA CLIENTE.
    IF EXISTS (
        SELECT
            TOP 1 *
        FROM
            FacturaCliente
        WITH
            (NOLOCK)
        WHERE
            IdVentaEstacion = @nIdVentaEstacion
            AND @nIdVentaEstacion > 0
    ) BEGIN
INSERT INTO @Log (Paso, Accion, Detalle)
VALUES (
    'DUPLICADO',
    'RETURN',
    LEFT(
        'Ya existe en FacturaCliente nIdVentaEstacion='
        + CONVERT(VARCHAR(12), ISNULL(@nIdVentaEstacion, 0))
        + ' nIdTurno=' + CONVERT(VARCHAR(12), ISNULL(@nIdTurno, 0))
        + ' nCanastilla=' + CONVERT(VARCHAR(12), ISNULL(@nCanastilla, 0)),
        1000
    )
)
BEGIN TRY INSERT INTO [dbo].[InvoiceFastLog] ([Fecha],[Paso],[Accion],[IdTurno],[IdVentaEstacion],[nCanastilla],[IdFacturaCliente],[CodigoArticulo],[CodigoManguera],[Detalle]) SELECT GETDATE(), Paso, Accion, @nIdTurno, @nIdVentaEstacion, @nCanastilla, @IdFacturaCliente, CodigoArticulo, CodigoManguera, Detalle FROM @Log END TRY BEGIN CATCH END CATCH
SELECT
    1 AS Resultado,
    'Ya existe esta venta en FACTURACLIENTE!!!' AS Mensaje,
    @NuevoNumeroFactura AS NUMFACURA,
    @IdResolucion AS IDRESOLUCION,
    @SecuencialIdVenta AS IDDOC,
    @IdFacturaCliente AS IdFacturaCliente,
    @PrefijoResolucion AS PrefijoFactura,
    @ClaveTecnicaResolucion AS ClaveTecnicaResolucion RETURN END BEGIN TRANSACTION
INSERT INTO @Log (Paso, Accion, Detalle)
VALUES (
    'TRANSACCION',
    'START',
    LEFT(
        'BEGIN TRANSACTION nIdVentaEstacion='
        + CONVERT(VARCHAR(12), ISNULL(@nIdVentaEstacion, 0))
        + ' nCanastilla=' + CONVERT(VARCHAR(12), ISNULL(@nCanastilla, 0)),
        1000
    )
)
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
    @SecuencialIdVenta = ISNULL(@SecuencialIdVenta, 0) + 1 END IF @nCalibracion = 0 BEGIN
    --si es ventatotal fleet o si viene en verdadero venta generanotaentrega
    IF @nTotalFleet = 1
    OR @bGeneraNotaEntrega = 1 BEGIN
SET
    @NumeroFacturaCompleto = ''
SET
    @NuevoNumeroFactura = 0
SET
    @IdResolucion = 0
SET
    @nFacturada = 0
SET
    @Resultado = 1 END ELSE IF @nCodFp <> 6
    OR @bCreditoFactura = 1 BEGIN IF @CodArea = 502 BEGIN IF ISNULL(@pNumeroFactura, '') <> '' BEGIN
SET
    @NumeroFacturaCompleto = @pNumeroFactura
SET
    @PrefijoResolucion = @pPrefijo
    --MARCA EXITOSO PARA CONTINUAR
SET
    @Resultado = 1
SET
    @nFacturada = 1 END ELSE BEGIN
    --GENERA NOTA ENTREGA
SET
    @nFacturada = 0
SET
    @IdResolucion = 0
SET
    @NuevoNumeroFactura = 0
SET
    @Resultado = 1 END END
    --COD ECUADOR o costa rica
    ELSE IF @CodArea = 593
    OR @CodArea = 506 BEGIN
SELECT
    TOP 1 @SecuencialFactura = FacturaCliente.SecuenciaVenta
FROM
    FacturaCliente
WHERE
    FacturaCliente.SecuenciaVenta <> 0
    AND FacturaCliente.CodigoIsla = @Isla
ORDER BY
    SecuenciaVenta DESC
    --si la secuencia de la tabla factura es > a la de configuracion inicial
    IF ISNULL(@SecuencialFactura, 0) > ISNULL(@SecuencialActualFactura, 0) BEGIN
SET
    @NuevoNumeroFactura = ISNULL(@SecuencialFactura, 0) + 1 END ELSE BEGIN
SET
    @NuevoNumeroFactura = ISNULL(@SecuencialActualFactura, 0) + 1 END
SET
    @NumeroFacturaCompleto = CONVERT(VARCHAR(MAX), @NuevoNumeroFactura)
    --MARCA EXITOSO PARA CONTINUAR
SET
    @Resultado = 1
SET
    @nFacturada = 1 END ELSE IF @CodArea = 809
    OR @CodArea = 51 --REPUBLICA DOMINICANA Y PERÚ
    BEGIN
    --SI @pNoValidarResolucion DEBE SETEAR LOS DATOS DIRECTOS QUE INGRESAN EN ESTE SP
    IF @pNoValidarResolucion = 1 BEGIN
SET
    @nFacturada = 1
SET
    @NumeroFacturaCompleto = @pNumeroFactura
SET
    @PrefijoResolucion = @pPrefijo
SET
    @IdResolucion = @pIdResolucion
SET
    @Resultado = 1
SET
    @nSecuenciaVenta = CONVERT(INT, RIGHT(@pNumeroFactura, 10)) END
    --SI ES RD Y NO ES CANASTILLA NO SE FACTURA
    ELSE IF @CodArea = 809
    AND @nCanastilla = 0 BEGIN
SET
    @nFacturada = 0
SET
    @IdResolucion = 0
SET
    @NuevoNumeroFactura = 0
SET
    @Resultado = 1 END ELSE BEGIN DECLARE @IdPuntoVentaResolucion INT
SET
    @IdPuntoVentaResolucion = @IdPuntoVenta IF @CodArea = 809 BEGIN
SET
    @IdPuntoVentaResolucion = 0 END IF EXISTS (
        SELECT
            *
        FROM
            Resolucion
        WITH
            (NOLOCK)
        WHERE
            Resolucion.IdCompania = @IdCompania
            AND CONVERT(INT, Resolucion.CodigoComprobante) = @CodComprobante
            AND Resolucion.IdCentroVenta = @IdCentroVenta
            AND Resolucion.IdPuntoVenta = @IdPuntoVentaResolucion
            AND Resolucion.EstadoResolucion = 1
    )
    AND @nCanastilla = 1 BEGIN
SELECT
    @UltimoNumeroAsignado = UltimoNumeroAsignado,
    @NumeroInicial = NumeroInicial,
    @FechaExpiracionResolucion = FechaExpiracionResolucion,
    @NumeroFinal = NumeroFinal,
    @IdResolucion = IdResolucion,
    @PrefijoResolucion = PrefijoFacturacion,
    @CodComprobante = CodigoComprobante
FROM
    Resolucion
WHERE
    IdCompania = @IdCompania
    AND CONVERT(INT, CodigoComprobante) = @CodComprobante
    AND IdCentroVenta = @IdCentroVenta
    AND IdPuntoVenta = @IdPuntoVentaResolucion
    AND EstadoResolucion = 1 IF @FechaExpiracionResolucion < CONVERT(DATE, GETDATE()) BEGIN
SET
    @ResultadoMensaje = 'Error : Hay una resolucion activa, pero la fecha de expiracion es menor a la fecha actual.'
SET
    @Resultado = 0 RAISERROR (@ResultadoMensaje, 16, 1) END
    --OBTIENE ULTIMO NUMERO ASIGNADO EN FACTURA PARA ESA RESOLUCION
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
    --ARMA EL NUMERO DE FACTURA COMPLETO
SET
    @NumeroFacturaCompleto = @PrefijoResolucion + @CodComprobante + RIGHT(
        '00000000' + LTRIM(RTRIM(CONVERT(VARCHAR(MAX), @NuevoNumeroFactura))),
        8
    )
UPDATE Resolucion
SET
    UltimoNumeroAsignado = @NuevoNumeroFactura
WHERE
    IdResolucion = @IdResolucion
SET
    @Resultado = 1
SET
    @nFacturada = 1 END END ELSE BEGIN
SET
    @ResultadoMensaje = 'Error : No se encontró resolucion activa para este punto de venta'
SET
    @Resultado = 0 RAISERROR (@ResultadoMensaje, 16, 1) END END ----FIN SI ES RD Y NO ES CANASTILLA NO SE FACTURA
    END ELSE BEGIN
    --1. Canastilla o maneja factura electronica DIAN, COLOMBIA (PENDIENTE 30 ENERO 2020)
    --2. Forma de pago diferente a credito (Panama o Honduras)
    --3. Forma de pago igual a credito, credito genera factura (Panama o Honduras)
    --4 @FacturarSiempre Si esta en 1 indica que si debe facturar.
    --5 @NoFacturarAuthAConsumidorFinal si es 1 valida que la identificacion del cliente no sea alguno de consumidor final , si es asi entonces no factura la venta
    DECLARE @forzarfacturacion INT = @FacturarSiempre DECLARE @ClientesIdentificacionPredeterminados NVARCHAR(MAX) = '9999999999999,1111111111111,2222222222,222222222222,999999999,9999999999';

-- Cadena de identificaciones separadas por comas
IF @NoFacturarAuthAConsumidorFinal = 1
AND CHARINDEX(
    @sIdentificacionCliente,
    @ClientesIdentificacionPredeterminados
) > 0 BEGIN
SET
    @forzarfacturacion = 0 END
    --si el TOTAL A PAGAR ES 0 ES POR QUE SE ESTA APLICANDO UN DESCUENTO POR EL MISMO VALOR
    IF ISNULL(@rTotalaPagar, 0) <= 0 BEGIN
SET
    @forzarfacturacion = 0 END IF @nCanastilla = 1
    OR (
        (
            (
                @nCodFp = 6
                AND @bCreditoFactura = 1
            )
            OR @nCodFp <> 6
        )
        AND (
            (
                @CodArea = 507
                AND @PANGenerarArchivo = 1
            )
            OR @CodArea = 504
        )
    )
    OR @forzarfacturacion = 1 BEGIN IF @CodArea = 57
    AND @COLValidarUVT = 1
    AND @COLValorUVT > 0
    AND @rSubtotal >= @COLValorUVT BEGIN
    --PARA A VALIDAR SI TENEMOS RESOLUCION FACTURA ELECTRONICA VIGENTE
    EXEC spValidateResolution @pIdCompania = @IdCompania,
    @pIsla = @Isla,
    @pCodComprobante = '18', --18 INDICA FACTURA ELECTRONICA
    @pIdCentroVenta = @IdCentroVenta,
    @pIdPuntoVenta = @IdPuntoVenta,
    @pCodArea = @CodArea,
    --output
    @pClaveTecnicaResolucion = @ClaveTecnicaResolucion OUTPUT,
    @pFechaExpiracionResolucion = @FechaExpiracionResolucion OUTPUT,
    @pNumeroFacturaCompleto = @NumeroFacturaCompleto OUTPUT,
    @pUltimoNumeroAsignado = @UltimoNumeroAsignado OUTPUT,
    @pNumeroInicial = @NumeroInicial OUTPUT,
    @pNumeroFinal = @NumeroFinal OUTPUT,
    @pIdResolucion = @IdResolucion OUTPUT,
    @pPrefijoResolucion = @PrefijoResolucion OUTPUT,
    @pNuevoNumeroFactura = @NuevoNumeroFactura OUTPUT,
    @pResult = @Resultado OUTPUT,
    @pMessage = @ResultadoMensaje OUTPUT
    --SI RESULT ES FALSE, INDICA QUE NO EXISTE UNA RESOLUCION ELECTRONICA VALIDA
    --POR LO TANTO SE DEBE EJECUTAR LA PARTE INFERIOR PARA BUSCAR LA RESOLUCION YA CON LOS 
    --PARAMETROS DE ENTRADA.
    IF @Resultado = 0 BEGIN PRINT @ResultadoMensaje
SET
    @IdResolucion = 0 END
SET
    @CodComprobante = '18'
SET
    @nTipoFactura = 18 END IF @IdResolucion <= 0 BEGIN
    --VALIDAR RESOLUCION
    EXEC spValidateResolution @pIdCompania = @IdCompania,
    @pIsla = @Isla,
    @pCodComprobante = @CodComprobante,
    @pIdCentroVenta = @IdCentroVenta,
    @pIdPuntoVenta = @IdPuntoVenta,
    @pCodArea = @CodArea,
    --output
    @pClaveTecnicaResolucion = @ClaveTecnicaResolucion OUTPUT,
    @pFechaExpiracionResolucion = @FechaExpiracionResolucion OUTPUT,
    @pNumeroFacturaCompleto = @NumeroFacturaCompleto OUTPUT,
    @pUltimoNumeroAsignado = @UltimoNumeroAsignado OUTPUT,
    @pNumeroInicial = @NumeroInicial OUTPUT,
    @pNumeroFinal = @NumeroFinal OUTPUT,
    @pIdResolucion = @IdResolucion OUTPUT,
    @pPrefijoResolucion = @PrefijoResolucion OUTPUT,
    @pNuevoNumeroFactura = @NuevoNumeroFactura OUTPUT,
    @pResult = @Resultado OUTPUT,
    @pMessage = @ResultadoMensaje OUTPUT END
    --SI @Resultado INDICA QUE spValidateResolution lo devolvio y por lo tanto 
    --la causa esta en la variable @ResultadoMensaje
    IF @Resultado = 0 BEGIN RAISERROR (@ResultadoMensaje, 16, 1) END
    -- si es ok
SET
    @nFacturada = 1 END
    --ELSE DE OTRAS CULTURAS
    ELSE BEGIN
SET
    @Resultado = 1
SET
    @NuevoNumeroFactura = 0
SET
    @IdResolucion = 0
SET
    @nFacturada = 0
SET
    @CodComprobante = NULL
SET
    @nTipoFactura = NULL END END END ELSE BEGIN
    --GENERA NOTA ENTREGA
SET
    @nFacturada = 0
SET
    @IdResolucion = 0
SET
    @NuevoNumeroFactura = 0
SET
    @Resultado = 1
SET
    @CodComprobante = NULL
SET
    @nTipoFactura = NULL END END ELSE BEGIN
    --NO GENERA NOTA ENTREGA
SET
    @nFacturada = 0
SET
    @IdResolucion = 0
SET
    @NuevoNumeroFactura = 0
SET
    @Resultado = 1
SET
    @ResultadoMensaje = 'VENTA DE CALIBRACION' END IF @Resultado = 0 BEGIN
INSERT INTO @Log (Paso, Accion, Detalle)
VALUES (
    'RESOLUCION',
    'FAIL',
    LEFT(
        ISNULL(@ResultadoMensaje, '')
        + ' resultado=' + CONVERT(VARCHAR(12), ISNULL(@Resultado, 0))
        + ' nFacturada=' + CONVERT(VARCHAR(12), ISNULL(@nFacturada, 0))
        + ' CodArea=' + CONVERT(VARCHAR(12), ISNULL(@CodArea, 0))
        + ' IdResolucion=' + CONVERT(VARCHAR(12), ISNULL(@IdResolucion, 0)),
        1000
    )
)
ROLLBACK
BEGIN TRY INSERT INTO [dbo].[InvoiceFastLog] ([Fecha],[Paso],[Accion],[IdTurno],[IdVentaEstacion],[nCanastilla],[IdFacturaCliente],[CodigoArticulo],[CodigoManguera],[Detalle]) SELECT GETDATE(), Paso, Accion, @nIdTurno, @nIdVentaEstacion, @nCanastilla, @IdFacturaCliente, CodigoArticulo, CodigoManguera, Detalle FROM @Log END TRY BEGIN CATCH END CATCH
SELECT
    @Resultado AS Resultado,
    @ResultadoMensaje AS Mensaje RETURN END IF @pNoValidarResolucion = 0 BEGIN
SET
    @nSecuenciaVenta = CONVERT(INT, @NuevoNumeroFactura) END
    --ASIGNA NULL'S EN CASO DE VACIO O CERO
    IF @IdResolucion = 0 BEGIN
SET
    @IdResolucion = NULL END IF @PrefijoResolucion = '' BEGIN
SET
    @PrefijoResolucion = NULL END
    --CREA CABECERA FACTURA.
INSERT INTO
    [dbo].[FacturaCliente] (
        [IdDocumento],
        [IdTurno],
        [IdTipoDocumento],
        [CodigoIsla],
        [Fecha],
        [HoraEntrega],
        [IdentificacionCliente],
        [NombreCliente],
        [IdResolucion],
        [PrefijoFactura],
        [NumeroFactura],
        [IdFormaPago],
        [FormasPago],
        [Placa],
        [Kilometraje],
        [TotalIVAS],
        [Subtotal],
        [ValorTotalFactura],
        [PorcentajeDescuento],
        [ValorDescuento],
        [Propina],
        [TotalICE],
        [ValorTotalSinSubsidioECU],
        [AhorroPorSubsidioECU],
        [RecaudoSUIC],
        [TotalaPagar],
        [CodigoElectronico],
        [CodigoCara],
        [CodigoManguera],
        [IdVentaEstacion],
        [SecuenciaVenta],
        [PuntosAcumulados],
        [FechaProximaRevicion],
        [TipoVenta],
        [TipoFactura],
        [TipoEmision],
        [Facturada],
        [Fidelizada],
        [Impresa],
        [DatosImpresionFactura],
        [IdentificacionConductor],
        [NombreConductor],
        [IdentPasaporte],
        [TotalFleet],
        [ROM],
        [VentaCHIPIslero],
        [FacturarConductor],
        [BarCodeAutomotor],
        [TipoAuth],
        [ImpuestoFijo],
        [ModoVenta],
        idtipovehiculo,
        Anulada,
        Descripcion,
        tipo_descuento
    )
VALUES
    (
        @SecuencialIdVenta,
        @nIdTurno,
        @nIdTipoDocumento,
        @Isla,
        @sFechaFormateada,
        @nHoraEntrega,
        @sIdentificacionCliente,
        @sNombreCliente,
        @IdResolucion,
        @PrefijoResolucion,
        @NumeroFacturaCompleto,
        @nCodFp,
        @sFormasPago,
        @sPlaca,
        @sKilometraje,
        @rTotalIVAS,
        @rSubtotal,
        @rValorTotalFactura,
        @rPorcentajeDescuento,
        @rValorDescuento,
        @rPropina,
        @rTotalICE,
        @rValorTotalSinSubsidioECU,
        @rAhorroPorSubsidioECU,
        @rRecaudoSUIC,
        @rTotalaPagar,
        @pCodigoElectronico,
        @nCodigoCara,
        @nCodigoManguera,
        @nIdVentaEstacion,
        @nSecuenciaVenta,
        @rPuntosAcumulados,
        @nFechaProximaRevicion,
        @nTipoVenta,
        @nTipoFactura,
        @nTipoEmision,
        @nFacturada,
        0,
        0,
        '',
        @sIdentificacionConductor,
        @sNombreConductor,
        @nIdentPasaporte,
        @nTotalFleet,
        @sROM,
        @nVentaCHIPIslero,
        @nFacturarConductor,
        @sBarCodeAutomotor,
        @sTipoAuth,
        @TotalImpuestoFijo,
        @ModeSale,
        @IdTipoVehiculo,
        @pAnulada,
        @pDescripcion,
        @TipoDescuento
    )
SET
    @IdFacturaCliente = @@IDENTITY --obtiene el idfacturacliente creado
INSERT INTO @Log (Paso, Accion, Detalle)
VALUES (
    'CABECERA',
    'INSERT',
    LEFT(
        'IdFacturaCliente=' + CONVERT(VARCHAR(12), ISNULL(@IdFacturaCliente, 0))
        + ' IdDocumento=' + CONVERT(VARCHAR(12), ISNULL(@SecuencialIdVenta, 0))
        + ' nTipoVenta=' + CONVERT(VARCHAR(12), ISNULL(@nTipoVenta, 0))
        + ' nFacturada=' + CONVERT(VARCHAR(12), ISNULL(@nFacturada, 0))
        + ' numFac=' + CONVERT(VARCHAR(12), ISNULL(@NuevoNumeroFactura, 0))
        + ' IdResolucion=' + CONVERT(VARCHAR(12), ISNULL(@IdResolucion, 0))
        + ' nIdVentaEstacion=' + CONVERT(VARCHAR(12), ISNULL(@nIdVentaEstacion, 0))
        + ' total=' + CONVERT(VARCHAR(24), ISNULL(@rValorTotalFactura, 0))
        + ' nCodFp=' + CONVERT(VARCHAR(12), ISNULL(@nCodFp, 0)),
        1000
    )
)
    IF @nCanastilla = 0 BEGIN
INSERT INTO @Log (Paso, Accion, Detalle)
VALUES (
    'RAMA_COMBUSTIBLE',
    'START',
    LEFT(
        'nCanastilla=0 idArt=' + CONVERT(VARCHAR(12), ISNULL(@IdArticuloDet, 0))
        + ' cant=' + CONVERT(VARCHAR(24), ISNULL(@CantidadDet, 0))
        + ' total=' + CONVERT(VARCHAR(24), ISNULL(@TotalDet, 0))
        + ' vUnit=' + CONVERT(VARCHAR(24), ISNULL(@ValorUnitarioDet, 0))
        + ' cara=' + CONVERT(VARCHAR(12), ISNULL(@nCodigoCara, 0))
        + ' manguera=' + CONVERT(VARCHAR(12), ISNULL(@nCodigoManguera, 0))
        + ' calib=' + CONVERT(VARCHAR(12), ISNULL(@nCalibracion, 0)),
        1000
    )
)
    --inserta el detalle combustible
INSERT INTO
    [dbo].[FacturaClienteDetalle] (
        [IdFacturaCliente],
        [IdDocumento],
        [IdTipoDocumento],
        [IdArticulo],
        [IdTarifaIVA],
        [Cantidad],
        [ValorUnitario],
        [PorcentajeIVA],
        [PorcentajeDescuento],
        [Subtotal],
        [ValorIVA],
        [Total],
        [ValorDescuento],
        [CodigoICE],
        [PorcentajeICE],
        [ValorICE],
        [FactorSubsidoECU],
        [PrecioSinSubsidioECU],
        [TipoIVA],
        [ImpuestoFijo]
    )
VALUES
    (
        @IdFacturaCliente,
        @SecuencialIdVenta,
        @nIdTipoDocumento,
        @IdArticuloDet,
        @IdTarifaIVADet,
        @CantidadDet,
        @ValorUnitarioDet,
        @PorcentajeIVADet,
        @PorcentajeDescuentoDet,
        @SubtotalDet,
        @ValorIVADet,
        @TotalDet,
        @ValorDescuentoDet,
        @CodigoICEDet,
        @PorcentajeICEDet,
        @ValorICEDet,
        @FactorSubsidoECUDet,
        @PrecioSinSubsidioECUDet,
        @TipoIVADet,
        @TotalImpuestoFijo
    )
INSERT INTO @Log (Paso, Accion, Detalle)
VALUES (
    'DETALLE_COMBUSTIBLE',
    'INSERT',
    LEFT(
        'idArt=' + CONVERT(VARCHAR(12), ISNULL(@IdArticuloDet, 0))
        + ' cant=' + CONVERT(VARCHAR(24), ISNULL(@CantidadDet, 0))
        + ' total=' + CONVERT(VARCHAR(24), ISNULL(@TotalDet, 0))
        + ' IdFacturaCliente=' + CONVERT(VARCHAR(12), ISNULL(@IdFacturaCliente, 0)),
        1000
    )
)
 END ELSE BEGIN
 IF CURSOR_STATUS('global', 'CursorDetalles') >= -1 BEGIN PRINT '1' CLOSE CursorDetalles DEALLOCATE CursorDetalles END DECLARE @XMLFacturaDetalle XML,
    @ServicioDetalle VARCHAR(1500),
    @transactionIDDetalle VARCHAR(50),
    @authotizationCodeDetale VARCHAR(50),
    @traceDetalle VARCHAR(50),
    @pinDetalle VARCHAR(50),
    @idtransaccionDetalle INT,
    @ticketDetalle VARCHAR(2500)
SET
    @XMLFacturaDetalle = @sXMLDetCanastilla
INSERT INTO @Log (Paso, Accion, Detalle)
VALUES (
    'RAMA_CANASTILLA',
    'START',
    LEFT(
        'nCanastilla=1 xmlLen=' + CONVERT(VARCHAR(12), ISNULL(LEN(@sXMLDetCanastilla), 0))
        + ' nodos=' + CONVERT(VARCHAR(12), ISNULL(@XMLFacturaDetalle.value('count(/Detalles/Detalle)', 'int'), 0))
        + ' IdFacturaCliente=' + CONVERT(VARCHAR(12), ISNULL(@IdFacturaCliente, 0))
        + ' nIdVentaEstacion=' + CONVERT(VARCHAR(12), ISNULL(@nIdVentaEstacion, 0)),
        1000
    )
)
    --inicio detalles
    --Se itera producto por producto de la venta de canastilla					
    DECLARE CursorDetalles CURSOR LOCAL FOR
SELECT
    CASE ISNULL(XmlFD.Col.value ('A[1]', 'varchar(max)'), 0)
        WHEN '' THEN '0'
        ELSE ISNULL(XmlFD.Col.value ('A[1]', 'VARCHAR(MAX)'), 0)
    END AS IdArticulo,
    CASE ISNULL(XmlFD.Col.value ('B[1]', 'varchar(max)'), 0)
        WHEN '' THEN '0'
        ELSE ISNULL(XmlFD.Col.value ('B[1]', 'VARCHAR(MAX)'), 0)
    END AS Cantidad,
    CASE ISNULL(XmlFD.Col.value ('C[1]', 'varchar(max)'), 0)
        WHEN '' THEN '0'
        ELSE ISNULL(XmlFD.Col.value ('C[1]', 'VARCHAR(MAX)'), 0)
    END AS IdTarifaIva,
    CASE ISNULL(XmlFD.Col.value ('D[1]', 'varchar(max)'), 0)
        WHEN '' THEN '0'
        ELSE ISNULL(XmlFD.Col.value ('D[1]', 'VARCHAR(MAX)'), 0)
    END AS ValorUnitario,
    CASE ISNULL(XmlFD.Col.value ('E[1]', 'varchar(max)'), 0)
        WHEN '' THEN '0'
        ELSE ISNULL(XmlFD.Col.value ('E[1]', 'VARCHAR(MAX)'), 0)
    END AS PorcentajeIva,
    CASE ISNULL(XmlFD.Col.value ('F[1]', 'varchar(max)'), 0)
        WHEN '' THEN '0'
        ELSE ISNULL(XmlFD.Col.value ('F[1]', 'VARCHAR(MAX)'), 0)
    END AS SubTotal,
    CASE ISNULL(XmlFD.Col.value ('G[1]', 'varchar(max)'), 0)
        WHEN '' THEN '0'
        ELSE ISNULL(XmlFD.Col.value ('G[1]', 'VARCHAR(MAX)'), 0)
    END AS ValorIva,
    CASE ISNULL(XmlFD.Col.value ('H[1]', 'varchar(max)'), 0)
        WHEN '' THEN '0'
        ELSE ISNULL(XmlFD.Col.value ('H[1]', 'VARCHAR(MAX)'), 0)
    END AS Total,
    CASE ISNULL(XmlFD.Col.value ('I[1]', 'varchar(max)'), 0)
        WHEN '' THEN '0'
        ELSE ISNULL(XmlFD.Col.value ('I[1]', 'VARCHAR(MAX)'), 0)
    END AS ValorDescuento,
    CASE ISNULL(XmlFD.Col.value ('J[1]', 'varchar(max)'), 0)
        WHEN '' THEN '0'
        ELSE ISNULL(XmlFD.Col.value ('J[1]', 'VARCHAR(MAX)'), 0)
    END AS CodigoICE,
    CASE ISNULL(XmlFD.Col.value ('K[1]', 'varchar(max)'), 0)
        WHEN '' THEN '0'
        ELSE ISNULL(XmlFD.Col.value ('K[1]', 'VARCHAR(MAX)'), 0)
    END AS PorcentajeICE,
    CASE ISNULL(XmlFD.Col.value ('L[1]', 'varchar(max)'), 0)
        WHEN '' THEN '0'
        ELSE ISNULL(XmlFD.Col.value ('L[1]', 'VARCHAR(MAX)'), 0)
    END AS ValorICE,
    CASE ISNULL(XmlFD.Col.value ('M[1]', 'varchar(max)'), 0)
        WHEN '' THEN '0'
        ELSE ISNULL(XmlFD.Col.value ('M[1]', 'VARCHAR(MAX)'), 0)
    END AS FactorSubsidio,
    CASE ISNULL(XmlFD.Col.value ('N[1]', 'varchar(max)'), 0)
        WHEN '' THEN '0'
        ELSE ISNULL(XmlFD.Col.value ('N[1]', 'VARCHAR(MAX)'), 0)
    END AS TipoIVA,
    CASE ISNULL(XmlFD.Col.value ('O[1]', 'varchar(max)'), '')
        WHEN '' THEN ''
        ELSE ISNULL(XmlFD.Col.value ('O[1]', 'VARCHAR(MAX)'), 0)
    END AS Servicio,
    CASE ISNULL(XmlFD.Col.value ('P[1]', 'varchar(max)'), '')
        WHEN '' THEN ''
        ELSE ISNULL(XmlFD.Col.value ('P[1]', 'VARCHAR(MAX)'), 0)
    END AS TransactionID,
    CASE ISNULL(XmlFD.Col.value ('Q[1]', 'varchar(max)'), '')
        WHEN '' THEN ''
        ELSE ISNULL(XmlFD.Col.value ('Q[1]', 'VARCHAR(MAX)'), 0)
    END AS TransactionCode,
    CASE ISNULL(XmlFD.Col.value ('R[1]', 'varchar(max)'), '')
        WHEN '' THEN ''
        ELSE ISNULL(XmlFD.Col.value ('R[1]', 'VARCHAR(MAX)'), 0)
    END AS Trace,
    CASE ISNULL(XmlFD.Col.value ('S[1]', 'varchar(max)'), '')
        WHEN '0' THEN ''
        ELSE ISNULL(XmlFD.Col.value ('S[1]', 'VARCHAR(MAX)'), 0)
    END AS PIN,
    CASE ISNULL(XmlFD.Col.value ('T[1]', 'varchar(max)'), '')
        WHEN '' THEN ''
        ELSE ISNULL(XmlFD.Col.value ('T[1]', 'VARCHAR(MAX)'), 0)
    END AS Idtransaccion,
    CASE ISNULL(XmlFD.Col.value ('U[1]', 'varchar(max)'), '')
        WHEN '' THEN ''
        ELSE ISNULL(XmlFD.Col.value ('U[1]', 'VARCHAR(MAX)'), 0)
    END AS Ticket
FROM
    @XMLFacturaDetalle.nodes ('/Detalles/Detalle') XmlFD (Col) OPEN CursorDetalles
FETCH NEXT
FROM
    CursorDetalles INTO @IdArticuloDet,
    @CantidadDet,
    @IdTarifaIVADet,
    @ValorUnitarioDet,
    @PorcentajeIVADet,
    @SubtotalDet,
    @ValorIVADet,
    @TotalDet,
    @ValorDescuentoDet,
    @CodigoICEDet,
    @PorcentajeICEDet,
    @ValorICEDet,
    @FactorSubsidoECUDet,
    @TipoIVADet,
    @ServicioDetalle,
    @transactionIDDetalle,
    @authotizationCodeDetale,
    @traceDetalle,
    @pinDetalle,
    @idtransaccionDetalle,
    @ticketDetalle WHILE @@FETCH_STATUS = 0 BEGIN
    --inserta el detalle canastilla
INSERT INTO
    [dbo].[FacturaClienteDetalle] (
        [IdFacturaCliente],
        [IdDocumento],
        [IdTipoDocumento],
        [IdArticulo],
        [IdTarifaIVA],
        [Cantidad],
        [ValorUnitario],
        [PorcentajeIVA],
        [PorcentajeDescuento],
        [Subtotal],
        [ValorIVA],
        [Total],
        [ValorDescuento],
        [CodigoICE],
        [PorcentajeICE],
        [ValorICE],
        [FactorSubsidoECU],
        [PrecioSinSubsidioECU],
        [TipoIVA]
    )
VALUES
    (
        @IdFacturaCliente,
        @SecuencialIdVenta,
        @nIdTipoDocumento,
        @IdArticuloDet,
        @IdTarifaIVADet,
        @CantidadDet,
        @ValorUnitarioDet,
        @PorcentajeIVADet,
        @PorcentajeDescuentoDet,
        @SubtotalDet,
        @ValorIVADet,
        @TotalDet,
        @ValorDescuentoDet,
        @CodigoICEDet,
        @PorcentajeICEDet,
        @ValorICEDet,
        @FactorSubsidoECUDet,
        @PrecioSinSubsidioECUDet,
        @TipoIVADet
    )
INSERT INTO @Log (Paso, Accion, Detalle)
VALUES (
    'DETALLE_CANASTILLA',
    'INSERT',
    LEFT(
        'idArt=' + CONVERT(VARCHAR(12), ISNULL(@IdArticuloDet, 0))
        + ' cant=' + CONVERT(VARCHAR(24), ISNULL(@CantidadDet, 0))
        + ' total=' + CONVERT(VARCHAR(24), ISNULL(@TotalDet, 0))
        + ' vUnit=' + CONVERT(VARCHAR(24), ISNULL(@ValorUnitarioDet, 0))
        + ' IdFacturaCliente=' + CONVERT(VARCHAR(12), ISNULL(@IdFacturaCliente, 0)),
        1000
    )
)
 IF ISNULL(@ServicioDetalle, '') <> '' BEGIN DECLARE @IdFacturaClienteDetalle INT = @@IDENTITY --obtiene el idfacturaclientedetalle creado
INSERT INTO
    [dbo].[facturaclientedetalleservicio] (
        [idfacturaclientedetalle],
        [servicio],
        [transactionId],
        [authorizationCode],
        [trace],
        [pin],
        [id_transaccion],
        [ticket]
    )
VALUES
    (
        @IdFacturaClienteDetalle,
        LEFT(@ServicioDetalle, 1500),
        LEFT(@transactionIDDetalle, 50),
        LEFT(@authotizationCodeDetale, 50),
        LEFT(@traceDetalle, 50),
        LEFT(@pinDetalle, 50),
        @idtransaccionDetalle,
        LEFT(@ticketDetalle, 2550)
    )
UPDATE facturacliente
SET
    panterapago = 1
WHERE
    IdFacturaCliente = @IdFacturaCliente END
--BUSCA ARTICULO
SELECT
    TOP 1 @CodArt = CodigoArticulo,
    @Articulo = Articulo
FROM
    Articulo
WITH
    (NOLOCK)
WHERE
    IdArticulo = @IdArticuloDet IF NOT EXISTS (
        SELECT
            *
        FROM
            AcumuladoraArticulo
        WITH
            (NOLOCK)
        WHERE
            IdTurno = @nIdTurno
            AND CodigoManguera = @nCodigoManguera
            AND CodigoArticulo = @CodArt
            AND Calibracion = @nCalibracion
    ) BEGIN
INSERT INTO
    [dbo].[AcumuladoraArticulo] (
        [IdTurno],
        [CodigoArticulo],
        [Calibracion],
        [CodigoManguera],
        [Articulo],
        [ValorUnitario],
        [Porcentaje],
        [Cantidad],
        [Valor],
        [CantidadVentas]
    )
VALUES
    (
        @nIdTurno,
        @CodArt,
        @nCalibracion,
        @nCodigoManguera,
        @Articulo,
        @ValorUnitarioDet,
        @PorcentajeIVADet,
        @CantidadDet,
        @TotalDet,
        1
    )
INSERT INTO @Log (Paso, Accion, CodigoArticulo, CodigoManguera, Detalle)
VALUES (
    'ACUMULADORA',
    'INSERT',
    @CodArt,
    @nCodigoManguera,
    LEFT(
        'INSERT turno=' + CONVERT(VARCHAR(12), ISNULL(@nIdTurno, 0))
        + ' idArt=' + CONVERT(VARCHAR(12), ISNULL(@IdArticuloDet, 0))
        + ' art=' + LEFT(ISNULL(@Articulo, ''), 40)
        + ' cant=' + CONVERT(VARCHAR(24), ISNULL(@CantidadDet, 0))
        + ' total=' + CONVERT(VARCHAR(24), ISNULL(@TotalDet, 0))
        + ' calib=' + CONVERT(VARCHAR(12), ISNULL(@nCalibracion, 0))
        + ' manguera=' + CONVERT(VARCHAR(12), ISNULL(@nCodigoManguera, 0)),
        1000
    )
)
 END ELSE BEGIN
UPDATE AcumuladoraArticulo
SET
    Cantidad = ISNULL(Cantidad, 0) + @CantidadDet,
    Valor = ISNULL(Valor, 0) + @TotalDet,
    CantidadVentas = ISNULL(CantidadVentas, 0) + 1
WHERE
    IdTurno = @nIdTurno
    AND CodigoManguera = @nCodigoManguera
    AND CodigoArticulo = @CodArt
    AND Calibracion = @nCalibracion
INSERT INTO @Log (Paso, Accion, CodigoArticulo, CodigoManguera, Detalle)
VALUES (
    'ACUMULADORA',
    'UPDATE',
    @CodArt,
    @nCodigoManguera,
    LEFT(
        'UPDATE turno=' + CONVERT(VARCHAR(12), ISNULL(@nIdTurno, 0))
        + ' idArt=' + CONVERT(VARCHAR(12), ISNULL(@IdArticuloDet, 0))
        + ' art=' + LEFT(ISNULL(@Articulo, ''), 40)
        + ' cant=' + CONVERT(VARCHAR(24), ISNULL(@CantidadDet, 0))
        + ' total=' + CONVERT(VARCHAR(24), ISNULL(@TotalDet, 0))
        + ' calib=' + CONVERT(VARCHAR(12), ISNULL(@nCalibracion, 0))
        + ' manguera=' + CONVERT(VARCHAR(12), ISNULL(@nCodigoManguera, 0)),
        1000
    )
)
 END
FETCH NEXT
FROM
    CursorDetalles INTO @IdArticuloDet,
    @CantidadDet,
    @IdTarifaIVADet,
    @ValorUnitarioDet,
    @PorcentajeIVADet,
    @SubtotalDet,
    @ValorIVADet,
    @TotalDet,
    @ValorDescuentoDet,
    @CodigoICEDet,
    @PorcentajeICEDet,
    @ValorICEDet,
    @FactorSubsidoECUDet,
    @TipoIVADet,
    @ServicioDetalle,
    @transactionIDDetalle,
    @authotizationCodeDetale,
    @traceDetalle,
    @pinDetalle,
    @idtransaccionDetalle,
    @ticketDetalle END --fin del while que recorre los xml detalle
    CLOSE CursorDetalles DEALLOCATE CursorDetalles
    --fin detalles
    END --fin si es o no canastilla
    --MODIFICA CONF INICIAL LA SECUENCIA DE LA FACTURA ACTUAL Y EL IDDOCUMENTO SI FUE FACTURADA.
    IF @nFacturada = 1 BEGIN
UPDATE ConfiguracionInicial
SET
    SecuenciaActualFactura = @NuevoNumeroFactura,
    SecuencialIdVenta = @SecuencialIdVenta
WHERE
    CodigoIsla = @Isla END ELSE BEGIN
    --SOLO MODIFICA EL IDDOCUMENTO
UPDATE ConfiguracionInicial
SET
    SecuencialIdVenta = @SecuencialIdVenta
WHERE
    CodigoIsla = @Isla END
INSERT INTO @Log (Paso, Accion, Detalle)
VALUES (
    'SECUENCIA',
    'UPDATE',
    LEFT(
        'nFacturada=' + CONVERT(VARCHAR(12), ISNULL(@nFacturada, 0))
        + ' IdDocumento=' + CONVERT(VARCHAR(12), ISNULL(@SecuencialIdVenta, 0))
        + ' numFac=' + CONVERT(VARCHAR(12), ISNULL(@NuevoNumeroFactura, 0))
        + ' isla=' + CONVERT(VARCHAR(12), ISNULL(@Isla, 0)),
        1000
    )
)
    --INSERTA DATOS DE PROCESAMIENTOS DE VENTA.
    IF @nCupo = 1 BEGIN
INSERT INTO @Log (Paso, Accion, Detalle)
VALUES (
    'CUPO',
    'INSERT',
    LEFT(
        'nCupo=1 IdDocumento=' + CONVERT(VARCHAR(12), ISNULL(@SecuencialIdVenta, 0))
        + ' nIdVentaEstacion=' + CONVERT(VARCHAR(12), ISNULL(@nIdVentaEstacion, 0))
        + ' cara=' + CONVERT(VARCHAR(12), ISNULL(@nCodigoCara, 0)),
        1000
    )
)
 DECLARE @IdVentaCupoString VARCHAR(MAX) = CONVERT(VARCHAR(MAX), @Isla) + '' + CONVERT(VARCHAR(MAX), @SecuencialIdVenta) DECLARE @IdVentaCupo INT = CONVERT(INT, @IdVentaCupoString)
INSERT INTO
    [dbo].[ControlProcesosPorVentaCupo] (
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
VALUES
    (
        @IdVentaCupo,
        @nTipoVenta,
        @nFechaZActiva,
        @nHoraTurnoActivo,
        0,
        @Isla,
        @nCodigoCara,
        @nIdCentroVentaCons,
        @nNumeroTurno,
        @nIdentificacionEmpelado,
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
        @sUsuarioFacturacion,
        @sPassFacturacion,
        @sIMEI,
        0,
        0,
        '',
        '',
        @nFechaVenta,
        0,
        @nHoraVenta,
        @nIdPuntoVentaCons,
        0,
        @nSincronizaSICOM,
        @nSincronizaSYSCOM
    ) END ELSE BEGIN
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
VALUES
    (
        @nIdTurno,
        @SecuencialIdVenta,
        @nTipoVenta,
        @nFechaZActiva,
        @nHoraTurnoActivo,
        0,
        @Isla,
        @nCodigoCara,
        @nIdCentroVentaCons,
        @nNumeroTurno,
        @nIdentificacionEmpelado,
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
        @sUsuarioFacturacion,
        @sPassFacturacion,
        @sIMEI,
        0,
        0,
        '',
        '',
        @nFechaVenta,
        0,
        @nHoraVenta,
        @nIdPuntoVentaCons,
        0,
        @nSincronizaSICOM,
        @nSincronizaSYSCOM
    ) END DECLARE @nIdFpInt INT = 0 IF @nRecaudo = 1 BEGIN IF @rRecaudoSUIC > 0 BEGIN
SELECT
    @nIdFpInt = [IdFormaPago]
FROM
    FormaPago
WITH
    (NOLOCK)
WHERE
    Codigo = 999 IF NOT EXISTS (
        SELECT
            *
        FROM
            AcumuladoraFormaPago
        WITH
            (NOLOCK)
        WHERE
            idTurno = @nIdTurno
            AND IdFormaPago = @nIdFpInt
    ) BEGIN
INSERT INTO
    [dbo].[AcumuladoraFormaPago] (
        [IdFormaPago],
        [idTurno],
        [NombreFormaPago],
        [Valor],
        [Codigo]
    )
VALUES
    (
        @nIdFpInt,
        @nIdTurno,
        @sFormasPago,
        @rValorTotalFactura,
        @nCodFp
    ) END ELSE BEGIN
UPDATE AcumuladoraFormaPago
SET
    Valor = ISNULL(Valor, 0) + @rValorTotalFactura
WHERE
    idTurno = @nIdTurno
    AND IdFormaPago = @nIdFpInt END END END
    --ACUMULADORA FORMA PAGO
SELECT
    @nIdFpInt = [IdFormaPago]
FROM
    FormaPago
WITH
    (NOLOCK)
WHERE
    Codigo = @nCodFp IF NOT EXISTS (
        SELECT
            *
        FROM
            AcumuladoraFormaPago
        WITH
            (NOLOCK)
        WHERE
            idTurno = @nIdTurno
            AND IdFormaPago = @nIdFpInt
    ) BEGIN
INSERT INTO
    [dbo].[AcumuladoraFormaPago] (
        [IdFormaPago],
        [idTurno],
        [NombreFormaPago],
        [Valor],
        [Codigo]
    )
VALUES
    (
        @nIdFpInt,
        @nIdTurno,
        @sFormasPago,
        @rValorTotalFactura,
        @nCodFp
    )
INSERT INTO @Log (Paso, Accion, Detalle)
VALUES (
    'ACUM_FP',
    'INSERT',
    LEFT(
        'idFp=' + CONVERT(VARCHAR(12), ISNULL(@nIdFpInt, 0))
        + ' nCodFp=' + CONVERT(VARCHAR(12), ISNULL(@nCodFp, 0))
        + ' fp=' + LEFT(ISNULL(@sFormasPago, ''), 30)
        + ' valor=' + CONVERT(VARCHAR(24), ISNULL(@rValorTotalFactura, 0)),
        1000
    )
)
 END ELSE BEGIN
UPDATE AcumuladoraFormaPago
SET
    Valor = ISNULL(Valor, 0) + @rValorTotalFactura
WHERE
    idTurno = @nIdTurno
    AND IdFormaPago = @nIdFpInt
INSERT INTO @Log (Paso, Accion, Detalle)
VALUES (
    'ACUM_FP',
    'UPDATE',
    LEFT(
        'idFp=' + CONVERT(VARCHAR(12), ISNULL(@nIdFpInt, 0))
        + ' nCodFp=' + CONVERT(VARCHAR(12), ISNULL(@nCodFp, 0))
        + ' fp=' + LEFT(ISNULL(@sFormasPago, ''), 30)
        + ' valor=' + CONVERT(VARCHAR(24), ISNULL(@rValorTotalFactura, 0)),
        1000
    )
)
 END COMMIT
INSERT INTO @Log (Paso, Accion, Detalle)
VALUES (
    'COMMIT',
    'OK',
    LEFT(
        'IdFacturaCliente=' + CONVERT(VARCHAR(12), ISNULL(@IdFacturaCliente, 0))
        + ' IdDocumento=' + CONVERT(VARCHAR(12), ISNULL(@SecuencialIdVenta, 0))
        + ' nIdVentaEstacion=' + CONVERT(VARCHAR(12), ISNULL(@nIdVentaEstacion, 0))
        + ' nCanastilla=' + CONVERT(VARCHAR(12), ISNULL(@nCanastilla, 0))
        + ' nFacturada=' + CONVERT(VARCHAR(12), ISNULL(@nFacturada, 0))
        + ' numFac=' + CONVERT(VARCHAR(12), ISNULL(@NuevoNumeroFactura, 0))
        + ' resultado=' + CONVERT(VARCHAR(12), ISNULL(@Resultado, 0))
        + ' total=' + CONVERT(VARCHAR(24), ISNULL(@rValorTotalFactura, 0))
        + ' msg=' + LEFT(ISNULL(@ResultadoMensaje, ''), 80),
        1000
    )
)
BEGIN TRY INSERT INTO [dbo].[InvoiceFastLog] ([Fecha],[Paso],[Accion],[IdTurno],[IdVentaEstacion],[nCanastilla],[IdFacturaCliente],[CodigoArticulo],[CodigoManguera],[Detalle]) SELECT GETDATE(), Paso, Accion, @nIdTurno, @nIdVentaEstacion, @nCanastilla, @IdFacturaCliente, CodigoArticulo, CodigoManguera, Detalle FROM @Log END TRY BEGIN CATCH END CATCH
    --RESULTADO
SELECT
    @Resultado AS Resultado,
    @ResultadoMensaje AS Mensaje,
    @NuevoNumeroFactura AS NUMFACURA,
    @IdResolucion AS IDRESOLUCION,
    @SecuencialIdVenta AS IDDOC,
    @IdFacturaCliente AS IdFacturaCliente,
    @PrefijoResolucion AS PrefijoFactura,
    @ClaveTecnicaResolucion AS ClaveTecnicaResolucion END TRY BEGIN CATCH
SET
    @InvoiceFastLogError = LEFT(ISNULL(ERROR_MESSAGE(), ''), 1000)
ROLLBACK
INSERT INTO @Log (Paso, Accion, Detalle)
VALUES (
    'CATCH',
    'ROLLBACK',
    LEFT(
        ISNULL(@InvoiceFastLogError, '')
        + ' nIdVentaEstacion=' + CONVERT(VARCHAR(12), ISNULL(@nIdVentaEstacion, 0))
        + ' nCanastilla=' + CONVERT(VARCHAR(12), ISNULL(@nCanastilla, 0))
        + ' IdFacturaCliente=' + CONVERT(VARCHAR(12), ISNULL(@IdFacturaCliente, 0))
        + ' IdDocumento=' + CONVERT(VARCHAR(12), ISNULL(@SecuencialIdVenta, 0)),
        1000
    )
)
BEGIN TRY INSERT INTO [dbo].[InvoiceFastLog] ([Fecha],[Paso],[Accion],[IdTurno],[IdVentaEstacion],[nCanastilla],[IdFacturaCliente],[CodigoArticulo],[CodigoManguera],[Detalle]) SELECT GETDATE(), Paso, Accion, @nIdTurno, @nIdVentaEstacion, @nCanastilla, @IdFacturaCliente, CodigoArticulo, CodigoManguera, Detalle FROM @Log END TRY BEGIN CATCH END CATCH
    --RESULTADO
SELECT
    0 AS Resultado,
    @InvoiceFastLogError AS Mensaje END CATCH END