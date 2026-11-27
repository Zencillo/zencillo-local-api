IF OBJECT_ID(N'dbo.usp_Upsert_ClienteOffLine_y_Placa', N'P') IS NOT NULL BEGIN DROP
PROCEDURE dbo.usp_Upsert_ClienteOffLine_y_Placa;

END;

GO CREATE
PROCEDURE dbo.usp_Upsert_ClienteOffLine_y_Placa @Identificacion NVARCHAR(50),
@NombreCliente NVARCHAR(200) = NULL,
@IdGrupoEmpresarial NVARCHAR(50) = NULL,
@GrupoEmpresarial NVARCHAR(150) = NULL,
@Telefono NVARCHAR(50) = NULL,
@Correo NVARCHAR(200) = NULL,
@DigVef NVARCHAR(10) = NULL,
@Verificado BIT = NULL,
@CodTipo NVARCHAR(50) = NULL,
@Placa NVARCHAR(20) = NULL,
@IdentificadorPlaca NVARCHAR(50) = NULL,
@CorreoPlaca NVARCHAR(200) = NULL
WITH
    ENCRYPTION AS BEGIN
SET
NOCOUNT ON;

SET
XACT_ABORT ON;

BEGIN TRY BEGIN TRANSACTION;

IF NOT EXISTS (
    SELECT
        1
    FROM
        dbo.ClienteOffLine
    WITH
        (UPDLOCK, HOLDLOCK)
    WHERE
        Identificacion = @Identificacion
) BEGIN
INSERT INTO
    dbo.ClienteOffLine (
        Identificacion,
        NombreCliente,
        IdGrupoEmpresarial,
        GrupoEmpresarial,
        Telefono,
        Correo,
        DigVef,
        Verificado,
        CodTipo
    )
VALUES
    (
        @Identificacion,
        @NombreCliente,
        @IdGrupoEmpresarial,
        @GrupoEmpresarial,
        @Telefono,
        @Correo,
        @DigVef,
        @Verificado,
        @CodTipo
    );

END ELSE BEGIN
UPDATE C
SET
    NombreCliente = COALESCE(NULLIF(@NombreCliente, ''), C.NombreCliente),
    IdGrupoEmpresarial = COALESCE(
        NULLIF(@IdGrupoEmpresarial, ''),
        C.IdGrupoEmpresarial
    ),
    GrupoEmpresarial = COALESCE(NULLIF(@GrupoEmpresarial, ''), C.GrupoEmpresarial),
    Telefono = COALESCE(NULLIF(@Telefono, ''), C.Telefono),
    Correo = COALESCE(NULLIF(@Correo, ''), C.Correo),
    DigVef = COALESCE(NULLIF(@DigVef, ''), C.DigVef),
    Verificado = COALESCE(@Verificado, C.Verificado),
    CodTipo = COALESCE(NULLIF(@CodTipo, ''), C.CodTipo)
FROM
    dbo.ClienteOffLine AS C
WHERE
    C.Identificacion = @Identificacion;

END;

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

COMMIT TRANSACTION;

END TRY BEGIN CATCH IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;

DECLARE @ErrMsg NVARCHAR(4000);

DECLARE @ErrNum INT;

DECLARE @ErrLine INT;

SELECT
    @ErrMsg = ERROR_MESSAGE(),
    @ErrNum = ERROR_NUMBER(),
    @ErrLine = ERROR_LINE();

RAISERROR (
    'usp_Upsert_ClienteOffLine_y_Placa | Error %d (Linea %d): %s',
    16,
    1,
    @ErrNum,
    @ErrLine,
    @ErrMsg
);

END CATCH;

END;

GO