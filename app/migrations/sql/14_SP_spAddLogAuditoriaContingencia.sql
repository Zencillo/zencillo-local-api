-- El procedimiento se elimina para permitir recrearlo.
IF OBJECT_ID(N'[dbo].[spAddLogAuditoriaContingencia]', N'P') IS NOT NULL BEGIN DROP
PROCEDURE [dbo].[spAddLogAuditoriaContingencia];

END GO
-- =============================================
-- Author:        WFGD
-- Create date: 29 ABRIL 2024
-- Description:    sp encrgado de guardaar registro de auditoria contingencia
-- =============================================
CREATE
PROCEDURE spAddLogAuditoriaContingencia
-- Add the parameters for the stored procedure here
@pProceso VARCHAR(50),
@pUsuario VARCHAR(50),
@pDescripcion VARCHAR(1000)
WITH
    ENCRYPTION AS BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
SET
NOCOUNT ON;

-- Insert statements for procedure here
INSERT INTO
    [dbo].[auditoria_contingencia] ([fecha], [proceso], [usuario], [descripcion])
VALUES
    (
        SYSDATETIME(),
        @pProceso,
        @pUsuario,
        @pDescripcion
    ) END GO