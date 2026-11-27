IF OBJECT_ID(N'dbo.halla_consecutivo_venta_pro', N'P') IS NOT NULL DROP
PROCEDURE dbo.halla_consecutivo_venta_pro;

GO CREATE
PROCEDURE dbo.halla_consecutivo_venta_pro @nIsla INT,
@nnumCapturador INT
WITH
    ENCRYPTION AS BEGIN
SET
NOCOUNT ON;

DECLARE @consecutivo INT = 0;

DECLARE @consecutivofinal INT = 0;

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

WHILE 1 = 1 BEGIN
SET
    @contador = @contador + 1;

IF @contador > @maxIntentos BEGIN
SELECT
    CAST(NULL AS INT) AS consecutivo,
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
    'OK: Consecutivo generado correctamente.' AS mensaje;

RETURN;

END;

END;

END;

GO