IF OBJECT_ID(N'dbo.Upsert_ClienteOffLine', N'P') IS NOT NULL DROP
PROCEDURE dbo.Upsert_ClienteOffLine;

GO CREATE
PROCEDURE dbo.Upsert_ClienteOffLine @Identificacion NVARCHAR(50),
@NombreCliente NVARCHAR(100) = NULL,
@IdGrupoEmpresarial INT = NULL,
@GrupoEmpresarial NVARCHAR(100) = NULL,
@Telefono NVARCHAR(50) = NULL,
@Correo NVARCHAR(100) = NULL,
@DigVef NVARCHAR(10) = NULL,
@Verificado INT = NULL,
@CodTipo INT = NULL
WITH
    ENCRYPTION AS BEGIN
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
    NombreCliente = CASE
        WHEN NULLIF(@NombreCliente, '') IS NULL THEN NombreCliente
        ELSE @NombreCliente
    END,
    IdGrupoEmpresarial = ISNULL(@IdGrupoEmpresarial, IdGrupoEmpresarial),
    GrupoEmpresarial = CASE
        WHEN NULLIF(@GrupoEmpresarial, '') IS NULL THEN GrupoEmpresarial
        ELSE @GrupoEmpresarial
    END,
    Telefono = CASE
        WHEN NULLIF(@Telefono, '') IS NULL THEN Telefono
        ELSE @Telefono
    END,
    Correo = CASE
        WHEN NULLIF(@Correo, '') IS NULL THEN Correo
        ELSE @Correo
    END,
    DigVef = CASE
        WHEN NULLIF(@DigVef, '') IS NULL THEN DigVef
        ELSE @DigVef
    END,
    Verificado = ISNULL(@Verificado, Verificado),
    CodTipo = ISNULL(@CodTipo, CodTipo)
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
        ISNULL(@NombreCliente, ''),
        ISNULL(@IdGrupoEmpresarial, 0),
        ISNULL(@GrupoEmpresarial, ''),
        ISNULL(@Telefono, ''),
        ISNULL(@Correo, ''),
        ISNULL(@DigVef, ''),
        ISNULL(@Verificado, 0),
        ISNULL(@CodTipo, 0)
    );

END;

END;

GO