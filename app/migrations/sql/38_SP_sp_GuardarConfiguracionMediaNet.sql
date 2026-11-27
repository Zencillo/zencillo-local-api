IF OBJECT_ID(N'dbo.sp_GuardarConfiguracionMediaNet', N'P') IS NOT NULL BEGIN DROP
PROCEDURE dbo.sp_GuardarConfiguracionMediaNet;

END;

GO CREATE
PROCEDURE dbo.sp_GuardarConfiguracionMediaNet @id INT = NULL,
@ip VARCHAR(50),
@mascara VARCHAR(50),
@gateway VARCHAR(50),
@hostPrinciR1Ip VARCHAR(50),
@hostPrinciR1Puerto VARCHAR(20),
@hostAlterR1Ip VARCHAR(50),
@hostAlterR1Puerto VARCHAR(20),
@hostPrinciR2Ip VARCHAR(50),
@hostPrinciR2Puerto VARCHAR(20),
@hostAlterR2Ip VARCHAR(50),
@hostAlterR2Puerto VARCHAR(20),
@puertoEscucha VARCHAR(20)
WITH
    ENCRYPTION AS BEGIN
SET
NOCOUNT ON;

IF @id IS NULL
OR NOT EXISTS (
    SELECT
        1
    FROM
        dbo.ConfiguracionMediaNet
    WHERE
        id = @id
) BEGIN
INSERT INTO
    dbo.ConfiguracionMediaNet (
        ip,
        mascara,
        gateway,
        hostPrinciR1Ip,
        hostPrinciR1Puerto,
        hostAlterR1Ip,
        hostAlterR1Puerto,
        hostPrinciR2Ip,
        hostPrinciR2Puerto,
        hostAlterR2Ip,
        hostAlterR2Puerto,
        puertoEscucha
    )
VALUES
    (
        @ip,
        @mascara,
        @gateway,
        @hostPrinciR1Ip,
        @hostPrinciR1Puerto,
        @hostAlterR1Ip,
        @hostAlterR1Puerto,
        @hostPrinciR2Ip,
        @hostPrinciR2Puerto,
        @hostAlterR2Ip,
        @hostAlterR2Puerto,
        @puertoEscucha
    );

SELECT
    CONVERT(INT, SCOPE_IDENTITY()) AS id;

END ELSE BEGIN
UPDATE dbo.ConfiguracionMediaNet
SET
    ip = @ip,
    mascara = @mascara,
    gateway = @gateway,
    hostPrinciR1Ip = @hostPrinciR1Ip,
    hostPrinciR1Puerto = @hostPrinciR1Puerto,
    hostAlterR1Ip = @hostAlterR1Ip,
    hostAlterR1Puerto = @hostAlterR1Puerto,
    hostPrinciR2Ip = @hostPrinciR2Ip,
    hostPrinciR2Puerto = @hostPrinciR2Puerto,
    hostAlterR2Ip = @hostAlterR2Ip,
    hostAlterR2Puerto = @hostAlterR2Puerto,
    puertoEscucha = @puertoEscucha
WHERE
    id = @id;

SELECT
    @id AS id;

END;

END;

GO