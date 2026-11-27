IF OBJECT_ID(N'dbo.SP_EJECUTAR_MIGRACIONES_BATCH', N'P') IS NOT NULL BEGIN DROP
PROCEDURE dbo.SP_EJECUTAR_MIGRACIONES_BATCH;

END;

DECLARE @ProcedureSql NVARCHAR(MAX);

SET
    @ProcedureSql = N'
CREATE PROCEDURE dbo.SP_EJECUTAR_MIGRACIONES_BATCH
(
    @Request XML
)
WITH ENCRYPTION
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @Queries TABLE
    (
        Id INT IDENTITY(1, 1) NOT NULL,
        Head NVARCHAR(200) NULL,
        QueryText NVARCHAR(MAX) NOT NULL
    );

    INSERT INTO @Queries
    (
        Head,
        QueryText
    )
    SELECT
        NULLIF(
            LTRIM(
                RTRIM(
                    Item.value(
                        ''(Head/text())[1]'',
                        ''NVARCHAR(200)''
                    )
                )
            ),
            N''''
        ),
        Item.value(
            ''(Query/text())[1]'',
            ''NVARCHAR(MAX)''
        )
    FROM @Request.nodes(
        ''/Request/Item''
    ) AS RequestData(Item);

    DECLARE @Id INT;
    DECLARE @Total INT;
    DECLARE @Head NVARCHAR(200);
    DECLARE @Query NVARCHAR(MAX);

    SET @Id = 1;

    SELECT
        @Total = COUNT(1)
    FROM @Queries;

    WHILE @Id <= @Total
    BEGIN
        SELECT
            @Head = Head,
            @Query = QueryText
        FROM @Queries
        WHERE Id = @Id;

        IF NULLIF(
            LTRIM(RTRIM(@Query)),
            N''''
        ) IS NOT NULL
        BEGIN
            BEGIN TRY
                EXEC sys.sp_executesql @Query;
            END TRY
            BEGIN CATCH
                DECLARE @ErrorMessage NVARCHAR(2048);

                SET @ErrorMessage =
                    N''Error ejecutando migración [''
                    + ISNULL(@Head, N''SIN_HEAD'')
                    + N'']. ''
                    + ERROR_MESSAGE()
                    + N'' Línea: ''
                    + CONVERT(
                        NVARCHAR(20),
                        ERROR_LINE()
                    );

                RAISERROR(
                    @ErrorMessage,
                    16,
                    1
                );

                RETURN;
            END CATCH;
        END;

        SET @Id = @Id + 1;
    END;
END;
';

EXEC sys.sp_executesql @ProcedureSql;