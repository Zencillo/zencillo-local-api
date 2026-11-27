IF OBJECT_ID(N'dbo.halla_consecutivo_venta_pro_v2', N'P') IS NOT NULL DROP
PROCEDURE dbo.halla_consecutivo_venta_pro_v2;

GO CREATE
PROCEDURE dbo.halla_consecutivo_venta_pro_v2 @nIsla INT,
@nnumCapturador INT,
@CodigoComprobante VARCHAR(10),
@CodigoArea INT
WITH
    ENCRYPTION AS BEGIN
SET
NOCOUNT ON;

DECLARE @consecutivo INT = 0;

DECLARE @consecutivofinal INT = 0;

DECLARE @FechaExpiracionResolucion DATE = NULL;

DECLARE @IdCentroVenta INT;

DECLARE @IdPuntoVenta INT;

DECLARE @maxIntentos INT = 100000;

DECLARE @contador INT = 0;

IF NOT EXISTS (
    SELECT
        1
    FROM
        dbo.ConfiguracionPOS
    WITH
        (NOLOCK)
    WHERE
        CodigoIsla = @nIsla
) BEGIN
SELECT
    CAST(NULL AS INT) AS consecutivo,
    CAST(NULL AS DATE) AS fechaExpiracionResolucion,
    'Error: No existe la isla especificada en ConfiguracionPOS.' AS mensaje;

RETURN;

END;

SELECT
    @consecutivo = ABS(ISNULL(ConsecutivoVentaEstacion, 0))
FROM
    dbo.ConfiguracionPOS
WITH
    (NOLOCK)
WHERE
    CodigoIsla = @nIsla;

SELECT
    @IdCentroVenta = idCVFacturacion,
    @IdPuntoVenta = idPVFacturacion
FROM
    dbo.ConfiguracionInicial
WITH
    (NOLOCK)
WHERE
    CodigoIsla = @nIsla;

IF @CodigoComprobante <> '0'
AND @CodigoArea = 57 BEGIN IF @IdCentroVenta IS NULL
OR @IdPuntoVenta IS NULL BEGIN
SELECT
    CAST(NULL AS INT) AS consecutivo,
    CAST(NULL AS DATE) AS fechaExpiracionResolucion,
    'Error: La isla no tiene configuración de facturación (idCVFacturacion/idPVFacturacion) en ConfiguracionInicial.' AS mensaje;

RETURN;

END;

SELECT
    TOP 1 @FechaExpiracionResolucion = R.FechaExpiracionResolucion
FROM
    dbo.Resolucion R
WITH
    (NOLOCK)
WHERE
    R.IdCentroVenta = @IdCentroVenta
    AND R.IdPuntoVenta = @IdPuntoVenta
    AND R.CodigoComprobante = @CodigoComprobante
ORDER BY
    R.FechaExpiracionResolucion DESC;

IF @FechaExpiracionResolucion IS NULL BEGIN
SELECT
    CAST(NULL AS INT) AS consecutivo,
    CAST(NULL AS DATE) AS fechaExpiracionResolucion,
    'Error: No existe una resolución para el centro/punto de venta y comprobante ' + @CodigoComprobante + '.' AS mensaje;

RETURN;

END;

IF CONVERT(DATE, GETDATE()) > @FechaExpiracionResolucion BEGIN
SELECT
    CAST(NULL AS INT) AS consecutivo,
    @FechaExpiracionResolucion AS fechaExpiracionResolucion,
    'Error: La resolución ha expirado (FechaExpiracionResolucion: ' + CONVERT(VARCHAR(10), @FechaExpiracionResolucion, 120) + ').' AS mensaje;

RETURN;

END;

END;

WHILE 1 = 1 BEGIN
SET
    @contador = @contador + 1;

IF @contador > @maxIntentos BEGIN
SELECT
    CAST(NULL AS INT) AS consecutivo,
    @FechaExpiracionResolucion AS fechaExpiracionResolucion,
    'Error: La numeración para la isla especificada ha expirado o se ha consumido completamente.' AS mensaje;

RETURN;

END;

SET
    @consecutivo = ISNULL(@consecutivo, 0) + 1;

SET
    @consecutivofinal = ISNULL(
        ABS(
            CONVERT(
                INT,
                CONVERT(VARCHAR(MAX), @nIsla) + CONVERT(VARCHAR(MAX), @consecutivo) + CONVERT(VARCHAR(MAX), @nnumCapturador)
            )
        ),
        0
    );

IF EXISTS (
    SELECT
        1
    FROM
        dbo.FacturaCliente
    WITH
        (NOLOCK)
    WHERE
        IdVentaEstacion = @consecutivofinal
) CONTINUE;

IF EXISTS (
    SELECT
        1
    FROM
        dbo.CheckVentasEstacion
    WITH
        (NOLOCK)
    WHERE
        IdVentaEstacion = @consecutivofinal
) CONTINUE;

IF NOT EXISTS (
    SELECT
        1
    FROM
        dbo.Venta
    WITH
        (NOLOCK)
    WHERE
        CodigoVenta = @consecutivofinal
) BEGIN
UPDATE dbo.ConfiguracionPOS
SET
    ConsecutivoVentaEstacion = @consecutivo
WHERE
    CodigoIsla = @nIsla;

SELECT
    @consecutivofinal AS consecutivo,
    @FechaExpiracionResolucion AS fechaExpiracionResolucion,
    'OK: Consecutivo generado correctamente.' AS mensaje;

RETURN;

END;

END;

END;

GO