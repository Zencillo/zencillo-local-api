IF OBJECT_ID(N'dbo.halla_consecutivo_venta', N'P') IS NOT NULL
    DROP PROCEDURE dbo.halla_consecutivo_venta;
GO

CREATE PROCEDURE dbo.halla_consecutivo_venta
    @nIsla INT,
    @nnumCapturador INT
WITH ENCRYPTION
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @consecutivo INT;
    DECLARE @consecutivofinal INT;
    DECLARE @valor VARCHAR(40);
    DECLARE @intentos INT;
    DECLARE @reiniciado BIT;
    DECLARE @maximo VARCHAR(10);

    SET @consecutivo = 0;
    SET @consecutivofinal = 0;
    SET @intentos = 0;
    SET @reiniciado = 0;
    SET @maximo = '2147483647';

    BEGIN TRY
        IF @nIsla IS NULL OR @nIsla <= 0
           OR @nnumCapturador IS NULL
           OR @nnumCapturador < 0
        BEGIN
            RAISERROR('Isla o capturador no valido.', 16, 1);
        END;

        BEGIN TRANSACTION;

        -- Bloquear configuracion hasta terminar
        SELECT @consecutivo = ConsecutivoVentaEstacion
        FROM dbo.ConfiguracionPOS WITH (UPDLOCK, HOLDLOCK)
        WHERE CodigoIsla = @nIsla;

        IF @@ROWCOUNT = 0
        BEGIN
            RAISERROR('No existe configuracion para la isla.', 16, 1);
        END;

        -- Corregir valores negativos
        IF @consecutivo IS NULL
            SET @consecutivo = 0;

        IF @consecutivo = -2147483648
            SET @consecutivo = 0;
        ELSE
            SET @consecutivo = ABS(@consecutivo);

        WHILE 1 = 1
        BEGIN
            SET @intentos = @intentos + 1;

            -- Proteccion contra ciclos infinitos
            IF @intentos > 1000000
            BEGIN
                RAISERROR('No se encontro consecutivo disponible.', 16, 1);
            END;

            -- Evitar overflow del propio consecutivo
            IF @consecutivo >= 2147483647
            BEGIN
                SET @consecutivo = 0;
                SET @reiniciado = 1;
            END;

            SET @consecutivo = @consecutivo + 1;

            -- Construir identificador como texto
            SET @valor =
                CONVERT(VARCHAR(20), @nIsla) +
                CONVERT(VARCHAR(20), @consecutivo) +
                CONVERT(VARCHAR(20), @nnumCapturador);

            -- Verificar limite INT antes de convertir
            IF LEN(@valor) > 10
               OR (
                   LEN(@valor) = 10
                   AND @valor COLLATE Latin1_General_BIN2
                       > @maximo COLLATE Latin1_General_BIN2
               )
            BEGIN
                -- Si ya reinicio y vuelve a exceder
                IF @reiniciado = 1
                BEGIN
                    RAISERROR('Se agoto el rango INT disponible.', 16, 1);
                END;

                -- Reiniciar consecutivo automaticamente
                SET @consecutivo = 0;
                SET @reiniciado = 1;
                CONTINUE;
            END;

            -- Conversion segura
            SET @consecutivofinal = CONVERT(INT, @valor);

            -- Validar FacturaCliente
            IF EXISTS (
                SELECT 1 FROM dbo.FacturaCliente
                WHERE IdVentaEstacion = @consecutivofinal
            )
            BEGIN
                CONTINUE;
            END;

            -- Validar CheckVentasEstacion
            IF EXISTS (
                SELECT 1 FROM dbo.CheckVentasEstacion
                WHERE IdVentaEstacion = @consecutivofinal
            )
            BEGIN
                CONTINUE;
            END;

            -- Validar Venta
            IF EXISTS (
                SELECT 1 FROM dbo.Venta
                WHERE CodigoVenta = @consecutivofinal
            )
            BEGIN
                CONTINUE;
            END;

            -- Se encontro un identificador disponible
            UPDATE dbo.ConfiguracionPOS
            SET ConsecutivoVentaEstacion = @consecutivo
            WHERE CodigoIsla = @nIsla;
            BREAK;
        END;

        COMMIT TRANSACTION;

        -- Mantener exactamente la respuesta original
        SELECT @consecutivofinal AS consecutivo;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        DECLARE @ErrorMessage NVARCHAR(4000);
        DECLARE @ErrorSeverity INT;
        DECLARE @ErrorState INT;

        SELECT
            @ErrorMessage = ERROR_MESSAGE(),
            @ErrorSeverity = ERROR_SEVERITY(),
            @ErrorState = ERROR_STATE();

        RAISERROR(@ErrorMessage, @ErrorSeverity, @ErrorState);
    END CATCH;
END;
GO
