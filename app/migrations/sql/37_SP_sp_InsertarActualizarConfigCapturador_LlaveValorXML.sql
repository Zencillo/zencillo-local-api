IF OBJECT_ID(
    N'dbo.sp_InsertarActualizarConfigCapturador_LlaveValorXML',
    N'P'
) IS NOT NULL BEGIN DROP
PROCEDURE dbo.sp_InsertarActualizarConfigCapturador_LlaveValorXML;

END;

GO CREATE
PROCEDURE dbo.sp_InsertarActualizarConfigCapturador_LlaveValorXML @XmlConfig XML
WITH
    ENCRYPTION AS BEGIN
SET
NOCOUNT ON;

DECLARE @Datos
TABLE (Llave NVARCHAR(200), Valor NVARCHAR(MAX));

INSERT INTO
    @Datos (Llave, Valor)
SELECT
    X.Item.value ('@Llave', 'NVARCHAR(200)'),
    X.Item.value ('@Valor', 'NVARCHAR(MAX)')
FROM
    @XmlConfig.nodes ('/Items/Item') AS X (Item);

UPDATE C
SET
    C.Valor = D.Valor
FROM
    dbo.ConfiguracionCapturador AS C
WITH
    (UPDLOCK)
    INNER JOIN @Datos AS D ON D.Llave = C.Llave
WHERE
    ISNULL(C.Valor, N'') <> ISNULL(D.Valor, N'');

INSERT INTO
    dbo.ConfiguracionCapturador (Llave, Valor)
SELECT
    D.Llave,
    D.Valor
FROM
    @Datos AS D
WHERE
    NOT EXISTS (
        SELECT
            1
        FROM
            dbo.ConfiguracionCapturador AS C
        WITH
            (HOLDLOCK, UPDLOCK)
        WHERE
            C.Llave = D.Llave
    );

END;

GO