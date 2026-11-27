IF OBJECT_ID(N'dbo.sp_UpsertClientePlacaOffLine', N'P') IS NOT NULL BEGIN DROP
PROCEDURE dbo.sp_UpsertClientePlacaOffLine;

END;

GO CREATE
PROCEDURE dbo.sp_UpsertClientePlacaOffLine @Placa NVARCHAR(50),
@IdentificadorPlaca NVARCHAR(100) = NULL,
@Identificacion NVARCHAR(100) = NULL,
@CorreoPlaca NVARCHAR(150) = NULL
WITH ENCRYPTION
AS BEGIN
SET
NOCOUNT ON;

IF NULLIF(@Placa, '') IS NOT NULL BEGIN IF EXISTS (
    SELECT
        1
    FROM
        dbo.ClientePlacaOffLine
    WITH
        (UPDLOCK, HOLDLOCK)
    WHERE
        Placa = @Placa
) BEGIN
UPDATE P
SET
    Identificador = COALESCE(NULLIF(@IdentificadorPlaca, ''), P.Identificador),
    Identificacion = COALESCE(NULLIF(@Identificacion, ''), P.Identificacion),
    Correo = COALESCE(NULLIF(@CorreoPlaca, ''), P.Correo)
FROM
    dbo.ClientePlacaOffLine AS P
WHERE
    P.Placa = @Placa;

END ELSE BEGIN
INSERT INTO
    dbo.ClientePlacaOffLine (Identificacion, Placa, Identificador, Correo)
VALUES
    (
        @Identificacion,
        @Placa,
        @IdentificadorPlaca,
        @CorreoPlaca
    );

END;

END;

END;

GO