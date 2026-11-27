IF OBJECT_ID(
    N'dbo.sp_InsertarActualizarConfigCapturador',
    N'P'
) IS NOT NULL BEGIN DROP
PROCEDURE dbo.sp_InsertarActualizarConfigCapturador;

END;

GO CREATE
PROCEDURE dbo.sp_InsertarActualizarConfigCapturador @Llave NVARCHAR(200),
@Valor NVARCHAR(MAX)
WITH
    ENCRYPTION AS BEGIN
SET
NOCOUNT ON;

UPDATE C
SET
    Valor = @Valor
FROM
    dbo.ConfiguracionCapturador AS C
WITH
    (UPDLOCK)
WHERE
    C.Llave = @Llave
    AND ISNULL(C.Valor, N'') <> ISNULL(@Valor, N'');

IF @@ROWCOUNT = 0 BEGIN
INSERT INTO
    dbo.ConfiguracionCapturador (Llave, Valor)
SELECT
    @Llave,
    @Valor
WHERE
    NOT EXISTS (
        SELECT
            1
        FROM
            dbo.ConfiguracionCapturador
        WITH
            (HOLDLOCK, UPDLOCK)
        WHERE
            Llave = @Llave
    );

END;

END;

GO