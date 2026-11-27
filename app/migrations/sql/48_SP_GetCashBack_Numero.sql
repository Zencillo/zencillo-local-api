-- Reinstala GetCashBack para filtrar por Numero de cashback en el turno.
IF OBJECT_ID(N'[dbo].[GetCashBack]', N'P') IS NOT NULL BEGIN DROP
PROCEDURE [dbo].[GetCashBack];

END GO CREATE
PROCEDURE [dbo].[GetCashBack]
@pIdTurno INT,
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
    IdTurno = @pIdTurno
    AND [IdCashBack] = ISNULL(@pIdCashBack, [IdCashBack])
    AND [Numero] = ISNULL(@pNumero, [Numero])
ORDER BY
    [IdCashBack] DESC END GO
