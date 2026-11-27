-- El procedimiento se elimina para permitir recrearlo.
IF OBJECT_ID(N'[dbo].[spSearchDiscountByRom]', N'P') IS NOT NULL BEGIN DROP
PROCEDURE [dbo].[spSearchDiscountByRom];

END GO CREATE
PROCEDURE [dbo].[spSearchDiscountByRom]
-- Add the parameters for the stored procedure here
@SearchItem VARCHAR(MAX),
@PumpFace VARCHAR(MAX),
@UnitValue DECIMAL(17, 7),
@Quantity DECIMAL(17, 7),
@Value DECIMAL(17, 7),
@PaymentMethodId INT,
@DiscountType VARCHAR(MAX),
@ArticleId INT,
@DiscountOUT DECIMAL(17, 7) OUTPUT,
@DiscountPercentageOUT DECIMAL(17, 7) OUTPUT
WITH
    ENCRYPTION AS BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
SET
NOCOUNT ON;

BEGIN TRY
SET
    @SearchItem = REPLACE(ISNULL(@SearchItem, ''), ' ', '') IF @SearchItem = '' BEGIN RETURN END DECLARE @CursorDiscountId INT,
    @CursorArticleId INT,
    @CursorDiscountType VARCHAR(50),
    @CursorPercentage DECIMAL(15, 3),
    @CursorStartDate DATETIME,
    @CursorEndDate DATETIME,
    @CursorStartHour INT,
    @CursorEndHour INT,
    @CursorIslandId INT,
    @CursorDispenserId INT,
    @CursorPumpFaceId INT,
    @CursorHoseId INT,
    @CursorDays VARCHAR(100),
    @CursorAllHours BIT,
    @CursorRound BIT,
    @CursorStatus BIT,
    @CursorValue DECIMAL(18, 3),
    @CursorAppliesPerUnit BIT,
    @CursorAllPaymentMethods BIT,
    @CursorPaymentMethodIds VARCHAR(200),
    @CursorItemIds VARCHAR(MAX),
    @CursorExcluyente BIT;

DECLARE DiscountCursor CURSOR LOCAL FOR
SELECT
    IdDescuento,
    IdArticulo,
    TipoDescuento,
    Porcentaje,
    FechaIni,
    FechaFin,
    HoraIni,
    HoraFin,
    IdIsla,
    IdSurtidor,
    IdCara,
    IdManguera,
    Dias,
    TodasHoras,
    Redondear,
    Estado,
    Valor,
    AplicaXUnidad,
    TodasLasFormasPago,
    IdFormasPago,
    ItemsId,
    ISNULL(excluyente, 0)
FROM
    dbo.Descuento
WITH
    (NOLOCK)
WHERE
    Estado = 1
    AND TipoDescuento = @DiscountType OPEN DiscountCursor;

FETCH NEXT
FROM
    DiscountCursor INTO @CursorDiscountId,
    @CursorArticleId,
    @CursorDiscountType,
    @CursorPercentage,
    @CursorStartDate,
    @CursorEndDate,
    @CursorStartHour,
    @CursorEndHour,
    @CursorIslandId,
    @CursorDispenserId,
    @CursorPumpFaceId,
    @CursorHoseId,
    @CursorDays,
    @CursorAllHours,
    @CursorRound,
    @CursorStatus,
    @CursorValue,
    @CursorAppliesPerUnit,
    @CursorAllPaymentMethods,
    @CursorPaymentMethodIds,
    @CursorItemIds,
    @CursorExcluyente;

WHILE @@FETCH_STATUS = 0 BEGIN
--se crea esta variable por que el continue con funciona bien y mejor de esta manera
DECLARE @validateDisccount BIT = 1 IF @CursorArticleId > 0
AND @CursorArticleId <> @ArticleId BEGIN
SET
    @validateDisccount = 0 END IF @validateDisccount = 1 BEGIN
SET
    @validateDisccount = 0 IF NOT EXISTS (
        SELECT
            Elemento
        FROM
            dbo.SplitString (@CursorItemIds, ';')
        WHERE
            Elemento = @SearchItem
    ) BEGIN
SET
    @validateDisccount = 0 END ELSE BEGIN
    --SI ENCONTRO EL DATO EN CURSORITEMS
SET
    @validateDisccount = 1 END IF @CursorExcluyente = 1
    AND @validateDisccount = 0 BEGIN
    --COMO EL DESCUENTO ES EXCLUYENTE ENTONCES SI NO LO ENCONTRO SIGNIFICA QUE DEBE APLICAR AL DESCUENTO
SET
    @validateDisccount = 1 END END IF @validateDisccount = 1 BEGIN EXEC spValidApplyDiscount @CursorDays,
    @CursorStartDate,
    @CursorEndDate,
    @CursorStartHour,
    @CursorEndHour,
    @CursorAllHours,
    @CursorPercentage,
    @CursorValue,
    @CursorPumpFaceId,
    @CursorAppliesPerUnit,
    @UnitValue,
    @Quantity,
    @Value,
    @PaymentMethodId,
    @CursorAllPaymentMethods,
    @CursorRound,
    @CursorPaymentMethodIds,
    @CursorDiscountId,
    @DiscountOUT OUTPUT,
    @DiscountPercentageOUT OUTPUT;

IF @DiscountOUT > 0 BEGIN BREAK END END
FETCH NEXT
FROM
    DiscountCursor INTO @CursorDiscountId,
    @CursorArticleId,
    @CursorDiscountType,
    @CursorPercentage,
    @CursorStartDate,
    @CursorEndDate,
    @CursorStartHour,
    @CursorEndHour,
    @CursorIslandId,
    @CursorDispenserId,
    @CursorPumpFaceId,
    @CursorHoseId,
    @CursorDays,
    @CursorAllHours,
    @CursorRound,
    @CursorStatus,
    @CursorValue,
    @CursorAppliesPerUnit,
    @CursorAllPaymentMethods,
    @CursorPaymentMethodIds,
    @CursorItemIds,
    @CursorExcluyente;

END CLOSE DiscountCursor;

DEALLOCATE DiscountCursor;

END TRY BEGIN CATCH
SET
    @DiscountOUT = 0
SET
    @DiscountPercentageOUT = 0 PRINT (ERROR_MESSAGE()) END CATCH END GO