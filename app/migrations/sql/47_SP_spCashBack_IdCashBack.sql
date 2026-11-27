-- Reinstala spCashBack para devolver IdCashBack al crear cashback exitosamente.
IF OBJECT_ID(N'[dbo].[spCashBack]', N'P') IS NOT NULL BEGIN DROP
PROCEDURE [dbo].[spCashBack];

END GO CREATE
PROCEDURE [dbo].[spCashBack]
@pIdTurno INT,
@pCodigoFP VARCHAR(5),
@pValor DECIMAL(17, 7),
@pFEE DECIMAL(17, 7),
@pTotal DECIMAL(17, 7),
@pIdentificacion VARCHAR(50),
@pNombre VARCHAR(100),
@pTelefono VARCHAR(20),
@pIncluyeVenta BIT,
@pIdDocumento INT,
@pSincronizado BIT
WITH
    ENCRYPTION AS BEGIN
SET
NOCOUNT ON;

DECLARE @NumberCashBack INT = 0,
@IdCashBack INT = 0,
@Procesado BIT = 0,
@MessageOUT VARCHAR(MAX) = '',
@bTransactionActived BIT = 0 BEGIN TRY BEGIN TRAN
SET
    @bTransactionActived = 1
SELECT
    @NumberCashBack = ISNULL(MAX(Numero), 0)
FROM
    [CashBackTurno]
WHERE
    IdTurno = @pIdTurno
SET
    @NumberCashBack = ISNULL(@NumberCashBack, 0) + 1
INSERT INTO
    [dbo].[CashBackTurno] (
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
    )
VALUES
    (
        @pIdTurno,
        @NumberCashBack,
        @pCodigoFP,
        @pValor,
        @pFEE,
        @pTotal,
        SYSDATETIME(),
        @pIdentificacion,
        @pNombre,
        @pTelefono,
        @pIncluyeVenta,
        @pIdDocumento,
        @pSincronizado
    )
SET
    @IdCashBack = CAST(SCOPE_IDENTITY() AS INT)
    IF EXISTS (
        SELECT
            *
        FROM
            AcmCashBackTurno
        WITH
            (nolock)
        WHERE
            IdTurno = @pIdTurno
            AND CodigoFP = @pCodigoFP
    ) BEGIN
UPDATE AcmCashBackTurno
SET
    Valor = ISNULL(VALOR, 0) + @pValor,
    Fee = ISNULL(FEE, 0) + @pFEE,
    Total = ISNULL(Total, 0) + @pTotal
WHERE
    IdTurno = @pIdTurno
    AND CodigoFP = @pCodigoFP END ELSE BEGIN
INSERT INTO
    [dbo].[AcmCashBackTurno] ([IdTurno], [CodigoFP], [Valor], [Fee], [Total])
VALUES
    (@pIdTurno, @pCodigoFP, @pValor, @pFEE, @pTotal) END COMMIT
SET
    @Procesado = 1
SET
    @MessageOUT = 'Operacion realizada satisfactoriamente.' END TRY BEGIN CATCH
SET
    @MessageOUT = ERROR_MESSAGE()
SET
    @Procesado = 0 IF @bTransactionActived = 1 BEGIN ROLLBACK END END CATCH
SELECT
    @Procesado AS Process,
    @MessageOUT AS [Message],
    @IdCashBack AS IdCashBack,
    @IdCashBack AS Id,
    @NumberCashBack AS NumberCashBack END GO
