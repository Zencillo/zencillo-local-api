-- Reinstala GetCashBack para consultar por IdCashBack sin exigir IdTurno.
IF OBJECT_ID(N'[dbo].[GetCashBack]', N'P') IS NOT NULL BEGIN DROP
PROCEDURE [dbo].[GetCashBack];

END GO CREATE
PROCEDURE [dbo].[GetCashBack]
@pIdTurno INT = NULL,
@pIdCashBack INT = NULL,
@pNumero INT = NULL,
@pTop INT
WITH
    ENCRYPTION AS BEGIN
SET
NOCOUNT ON;

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
