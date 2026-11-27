IF OBJECT_ID(N'dbo.InsertarFormaPagoSiNoExiste', N'P') IS NOT NULL BEGIN DROP
PROCEDURE dbo.InsertarFormaPagoSiNoExiste;

END;

GO CREATE
PROCEDURE dbo.InsertarFormaPagoSiNoExiste @IdFormaPago INT,
@Nombre NVARCHAR(100),
@Codigo INT
WITH
    ENCRYPTION AS BEGIN
SET
NOCOUNT ON;

IF NOT EXISTS (
    SELECT
        1
    FROM
        dbo.FormaPago
    WHERE
        IdFormaPago = @IdFormaPago
        OR Codigo = @Codigo
) BEGIN
INSERT INTO
    dbo.FormaPago (IdFormaPago, Nombre, Codigo)
VALUES
    (@IdFormaPago, @Nombre, @Codigo);

END;

END;

GO