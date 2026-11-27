-- El procedimiento se elimina para permitir recrearlo.
IF OBJECT_ID(N'[dbo].[GetCashBack]', N'P') IS NOT NULL BEGIN DROP
PROCEDURE [dbo].[GetCashBack];

END GO CREATE
PROCEDURE [dbo].[GetCashBack]
-- Add the parameters for the stored procedure here
@pIdTurno INT = NULL,
@pIdCashBack INT = NULL,
@pNumero INT = NULL,
@pTop INT
WITH
    ENCRYPTION AS BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
SET
NOCOUNT ON;

-- Insert statements for procedure here
SELECT
    TOP (@pTop) [IdCashBack],
    [IdTurno],
    [Numero],
    [CodigoFp],
    [Valor],
    [Fee],
    [Total],
    [Fecha],
    [Identificacion],
    [Nombre],
    [Telefono],
    [IncluyeVenta],
    [IdDocumento],
    [Sincronizado]
FROM
    [dbo].[CashBackTurno]
WITH
    (NOLOCK)
WHERE
    (@pIdTurno IS NULL OR IdTurno = @pIdTurno)
    AND (@pIdCashBack IS NULL OR [IdCashBack] = @pIdCashBack)
    AND (@pNumero IS NULL OR [Numero] = @pNumero)
ORDER BY
    [IdCashBack] DESC END GO