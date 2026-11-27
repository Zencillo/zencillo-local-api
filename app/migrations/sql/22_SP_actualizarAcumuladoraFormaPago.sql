IF OBJECT_ID(N'dbo.actualizarAcumuladoraFormaPago', N'P') IS NOT NULL BEGIN DROP
PROCEDURE dbo.actualizarAcumuladoraFormaPago;

END;

GO CREATE
PROCEDURE dbo.actualizarAcumuladoraFormaPago @IdTurno INT,
@CodFp VARCHAR(MAX),
@Valor DECIMAL(17, 7)
WITH
    ENCRYPTION AS BEGIN
SET
NOCOUNT ON;

DECLARE @IdFp INT = 0;

DECLARE @NombreFP VARCHAR(MAX);

SELECT
    TOP 1 @IdFp = IdFormaPago,
    @NombreFP = Nombre
FROM
    dbo.FormaPago
WITH
    (NOLOCK)
WHERE
    Codigo = @CodFp;

IF EXISTS (
    SELECT
        1
    FROM
        dbo.AcumuladoraFormaPago
    WITH
        (NOLOCK)
    WHERE
        IdTurno = @IdTurno
        AND Codigo = @CodFp
) BEGIN
UPDATE dbo.AcumuladoraFormaPago
SET
    IdFormaPago = @IdFp,
    NombreFormaPago = @NombreFP,
    Valor = ISNULL(Valor, 0) + @Valor,
    Codigo = @CodFp
WHERE
    IdTurno = @IdTurno
    AND Codigo = @CodFp;

END ELSE BEGIN
INSERT INTO
    dbo.AcumuladoraFormaPago (
        IdFormaPago,
        IdTurno,
        NombreFormaPago,
        Valor,
        Codigo
    )
VALUES
    (@IdFp, @IdTurno, @NombreFP, @Valor, @CodFp);

END;

END;

GO