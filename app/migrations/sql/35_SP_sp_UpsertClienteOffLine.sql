IF OBJECT_ID(N'dbo.sp_UpsertClienteOffLine', N'P') IS NOT NULL DROP
PROCEDURE dbo.sp_UpsertClienteOffLine;

GO CREATE
PROCEDURE dbo.sp_UpsertClienteOffLine @Identificacion NVARCHAR(50),
@NombreCliente NVARCHAR(200) = NULL,
@IdGrupoEmpresarial INT = NULL,
@GrupoEmpresarial NVARCHAR(200) = NULL,
@Telefono NVARCHAR(50) = NULL,
@Correo NVARCHAR(200) = NULL,
@DigVef NVARCHAR(5) = NULL,
@Verificado BIT = NULL,
@CodTipo NVARCHAR(50) = NULL
WITH ENCRYPTION
AS BEGIN
SET
NOCOUNT ON;

IF EXISTS (
    SELECT
        1
    FROM
        dbo.ClienteOffLine
    WHERE
        Identificacion = @Identificacion
) BEGIN
UPDATE dbo.ClienteOffLine
SET
    NombreCliente = COALESCE(NULLIF(@NombreCliente, ''), NombreCliente),
    IdGrupoEmpresarial = COALESCE(@IdGrupoEmpresarial, IdGrupoEmpresarial),
    GrupoEmpresarial = COALESCE(NULLIF(@GrupoEmpresarial, ''), GrupoEmpresarial),
    Telefono = COALESCE(NULLIF(@Telefono, ''), Telefono),
    Correo = COALESCE(NULLIF(@Correo, ''), Correo),
    DigVef = COALESCE(NULLIF(@DigVef, ''), DigVef),
    Verificado = COALESCE(@Verificado, Verificado),
    CodTipo = COALESCE(NULLIF(@CodTipo, ''), CodTipo)
WHERE
    Identificacion = @Identificacion;

END ELSE BEGIN
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

END;

END;

GO