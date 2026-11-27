IF OBJECT_ID(N'dbo.SP_EJECUTAR_QUERIES_BATCH', N'P') IS NOT NULL BEGIN DROP
PROCEDURE dbo.SP_EJECUTAR_QUERIES_BATCH;

END;

GO CREATE
PROCEDURE dbo.SP_EJECUTAR_QUERIES_BATCH (@Request XML)
WITH ENCRYPTION
AS BEGIN
SET
NOCOUNT ON;

DECLARE @Queries
TABLE (
    Id INT IDENTITY(1, 1),
    Head NVARCHAR(200),
    QueryText NVARCHAR(MAX)
);

INSERT INTO
    @Queries (Head, QueryText)
SELECT
    Item.value ('(Head/text())[1]', 'NVARCHAR(200)'),
    Item.value ('(Query/text())[1]', 'NVARCHAR(MAX)')
FROM
    @Request.nodes ('/Request/Item') AS RequestData (Item);

/*
 * Primer ResultSet:
 * listado y orden de las consultas recibidas.
 */
SELECT
    Id,
    Head
FROM
    @Queries
ORDER BY
    Id;

DECLARE @Id INT = 1;

DECLARE @Total INT;

DECLARE @Query NVARCHAR(MAX);

SELECT
    @Total = COUNT(*)
FROM
    @Queries;

/*
 * Cada consulta se ejecuta como un batch independiente.
 * Cada ejecución puede devolver su propio ResultSet.
 */
WHILE @Id <= @Total BEGIN
SELECT
    @Query = QueryText
FROM
    @Queries
WHERE
    Id = @Id;

IF NULLIF(LTRIM(RTRIM(@Query)), N'') IS NOT NULL BEGIN EXEC sys.sp_executesql @Query;

END;

SET
    @Id = @Id + 1;

END;

END;

GO