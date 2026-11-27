-- El procedimiento se elimina para permitir recrearlo.
IF OBJECT_ID(N'[dbo].[spObtenerNumeroFactura]', N'P') IS NOT NULL
BEGIN
    DROP PROCEDURE [dbo].[spObtenerNumeroFactura];
END
GO

CREATE PROCEDURE [dbo].[spObtenerNumeroFactura]
    @Isla INT,
    @IdCompania INT,
    @IdCentroVenta INT,
    @IdPuntoVenta INT,
    @CodComprobante VARCHAR(MAX),
    @CodArea INT,
    @nCanastilla INT,
    @pNumeroFactura VARCHAR(50) = NULL,
    @pPrefijo VARCHAR(10) = NULL,
    @pIdResolucion INT = 0,
    @pNoValidarResolucion BIT = 0,
    @pActualizarResolution BIT = 0,

    -- OUTPUTS
    @NumeroFacturaCompleto VARCHAR(MAX) OUTPUT,
    @NuevoNumeroFactura INT OUTPUT,
    @FechaExpiracionResolucion DATE OUTPUT,
    @IdResolucion INT OUTPUT,
    @PrefijoResolucion VARCHAR(MAX) OUTPUT,
    @Resultado INT OUTPUT,
    @ResultadoMensaje VARCHAR(MAX) OUTPUT

WITH ENCRYPTION
AS
BEGIN
    SET NOCOUNT ON;

    -- Declaración de variables
    DECLARE @SecuencialFactura INT = 0;
    DECLARE @SecuencialActualFactura INT = 0;
    DECLARE @UltimoNumeroAsignado INT;
    DECLARE @NumeroInicial INT;
    DECLARE @NumeroFinal INT;

    -- Inicialización de resultados
    SET @Resultado = 0;
    SET @NumeroFacturaCompleto = '';
    SET @NuevoNumeroFactura = 0;
    SET @IdResolucion = 0;
    SET @PrefijoResolucion = '';
    SET @ResultadoMensaje = '';

    -- Obtener la secuencia actual desde configuración inicial
    SELECT
        @SecuencialActualFactura = SecuenciaActualFactura
    FROM ConfiguracionInicial
    WHERE CodigoIsla = @Isla;


    ------------------------------------------------------------
    -- GTM (Guatemala)
    ------------------------------------------------------------
    IF @CodArea = 502
    BEGIN
        IF ISNULL(@pNumeroFactura, '') <> ''
        BEGIN
            SET @NumeroFacturaCompleto = @pNumeroFactura;
            SET @PrefijoResolucion = @pPrefijo;
            SET @IdResolucion = @pIdResolucion;
            SET @Resultado = 1;
            SET @NuevoNumeroFactura = 0;
        END
        ELSE
        BEGIN
            SET @Resultado = 1;
            SET @NuevoNumeroFactura = 0;
            SET @NumeroFacturaCompleto = '';
        END

        RETURN;
    END


    ------------------------------------------------------------
    -- Ecuador / Costa Rica
    ------------------------------------------------------------
    IF @CodArea = 593 OR @CodArea = 506
    BEGIN
        SELECT TOP 1
            @SecuencialFactura = SecuenciaVenta
        FROM FacturaCliente
        WHERE SecuenciaVenta <> 0
          AND CodigoIsla = @Isla
        ORDER BY SecuenciaVenta DESC;

        IF ISNULL(@SecuencialFactura, 0) > ISNULL(@SecuencialActualFactura, 0)
        BEGIN
            SET @NuevoNumeroFactura = ISNULL(@SecuencialFactura, 0) + 1;
        END
        ELSE
        BEGIN
            SET @NuevoNumeroFactura = ISNULL(@SecuencialActualFactura, 0) + 1;
        END

        SET @NumeroFacturaCompleto = CONVERT(VARCHAR(MAX), @NuevoNumeroFactura);
        SET @Resultado = 1;

        RETURN;
    END


    ------------------------------------------------------------
    -- República Dominicana / Perú / Panamá
    ------------------------------------------------------------
    IF @CodArea = 809 OR @CodArea = 51 OR @CodArea = 507
    BEGIN

        -- No validar resolución
        IF @pNoValidarResolucion = 1
        BEGIN
            SET @NumeroFacturaCompleto = @pNumeroFactura;
            SET @PrefijoResolucion = @pPrefijo;
            SET @IdResolucion = @pIdResolucion;
            SET @Resultado = 1;

            RETURN;
        END

        -- República Dominicana sin canastilla
        ELSE IF @CodArea = 809 AND @nCanastilla = 0
        BEGIN
            SET @Resultado = 1;
            SET @NuevoNumeroFactura = 0;
            SET @NumeroFacturaCompleto = '';

            RETURN;
        END

        ELSE
        BEGIN
            DECLARE @IdPuntoVentaResolucion INT;

            SET @IdPuntoVentaResolucion =
                CASE
                    WHEN @CodArea = 809 THEN 0
                    ELSE @IdPuntoVenta
                END;

            -- Validar existencia de resolución activa
            IF EXISTS
            (
                SELECT 1
                FROM Resolucion WITH (NOLOCK)
                WHERE IdCompania = @IdCompania
                  AND CONVERT(INT, CodigoComprobante) = @CodComprobante
                  AND IdCentroVenta = @IdCentroVenta
                  AND IdPuntoVenta = @IdPuntoVentaResolucion
                  AND EstadoResolucion = 1
                  AND @nCanastilla = 1
            )
            BEGIN

                -- Obtener información de la resolución
                SELECT TOP 1
                    @UltimoNumeroAsignado = UltimoNumeroAsignado,
                    @NumeroInicial = NumeroInicial,
                    @FechaExpiracionResolucion = FechaExpiracionResolucion,
                    @NumeroFinal = NumeroFinal,
                    @IdResolucion = IdResolucion,
                    @PrefijoResolucion = PrefijoFacturacion,
                    @CodComprobante = CodigoComprobante
                FROM Resolucion
                WHERE IdCompania = @IdCompania
                  AND CONVERT(INT, CodigoComprobante) = @CodComprobante
                  AND IdCentroVenta = @IdCentroVenta
                  AND IdPuntoVenta = @IdPuntoVentaResolucion
                  AND EstadoResolucion = 1;

                -- Validar fecha de expiración
                IF @FechaExpiracionResolucion < CONVERT(DATE, GETDATE())
                BEGIN
                    SET @ResultadoMensaje =
                        'Error: Hay una resolución activa, pero la fecha de expiración es menor a la fecha actual.';

                    SET @Resultado = 0;

                    RETURN;
                END

                -- Obtener último secuencial facturado
                SELECT TOP 1
                    @SecuencialFactura = SecuenciaVenta
                FROM FacturaCliente
                WHERE IdResolucion = @IdResolucion
                ORDER BY SecuenciaVenta DESC;

                -- Calcular nuevo número de factura
                IF ISNULL(@SecuencialFactura, 0) > ISNULL(@UltimoNumeroAsignado, 0)
                BEGIN
                    SET @NuevoNumeroFactura = ISNULL(@SecuencialFactura, 0) + 1;
                END
                ELSE
                BEGIN
                    IF ISNULL(@NumeroInicial, 0) > ISNULL(@UltimoNumeroAsignado, 0)
                    BEGIN
                        SET @NuevoNumeroFactura = ISNULL(@NumeroInicial, 1);
                    END
                    ELSE
                    BEGIN
                        SET @NuevoNumeroFactura = ISNULL(@UltimoNumeroAsignado, 0) + 1;
                    END
                END

                -- Validar límite de numeración
                IF @NuevoNumeroFactura > @NumeroFinal
                BEGIN
                    SET @ResultadoMensaje =
                        'Error: Número actual '
                        + CONVERT(VARCHAR(MAX), @NuevoNumeroFactura)
                        + ' supera al número final permitido '
                        + CONVERT(VARCHAR(MAX), @NumeroFinal);

                    SET @Resultado = 0;

                    RETURN;
                END

                -- Construcción del número de factura (8 dígitos)
                SET @NumeroFacturaCompleto =
                    @PrefijoResolucion
                    + @CodComprobante
                    + RIGHT(
                        '00000000'
                        + LTRIM(RTRIM(CONVERT(VARCHAR(MAX), @NuevoNumeroFactura))),
                        8
                    );

                -- Comprobantes especiales (10 dígitos)
                IF @CodComprobante IN ('31', '32', '44', '45')
                BEGIN
                    SET @NumeroFacturaCompleto =
                        @PrefijoResolucion
                        + @CodComprobante
                        + RIGHT(
                            '0000000000'
                            + LTRIM(RTRIM(CONVERT(VARCHAR(MAX), @NuevoNumeroFactura))),
                            10
                        );
                END

                -- Actualizar último número de resolución
                IF @pActualizarResolution = 1
                BEGIN
                    UPDATE Resolucion
                    SET UltimoNumeroAsignado = @NuevoNumeroFactura
                    WHERE IdResolucion = @IdResolucion;
                END

                SET @Resultado = 1;

                RETURN;
            END
            ELSE
            BEGIN
                SET @ResultadoMensaje =
                    'Error: No se encontró resolución activa para este punto de venta';

                SET @Resultado = 0;

                RETURN;
            END
        END
    END


    ------------------------------------------------------------
    -- Default / fallback: culturas no incluidas
    ------------------------------------------------------------
    SET @Resultado = 1;
    SET @NumeroFacturaCompleto = '';
    SET @NuevoNumeroFactura = 0;

    RETURN;
END
GO