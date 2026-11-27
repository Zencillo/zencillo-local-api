-- El procedimiento se elimina para permitir recrearlo.
IF OBJECT_ID(N'[dbo].[spFindDiscountByItem]', N'P') IS NOT NULL BEGIN DROP
PROCEDURE [dbo].[spFindDiscountByItem];

END GO CREATE
PROCEDURE [dbo].[spFindDiscountByItem]
-- Add the parameters for the stored procedure here
@ArticleId INT,
@PumpFace VARCHAR(MAX),
@UnitValue DECIMAL(17, 7),
@Quantity DECIMAL(17, 7),
@Value DECIMAL(17, 7),
@PaymentMethodId INT,
--output variables
@Discount DECIMAL(17, 7) OUTPUT,
@DiscountPercentage DECIMAL(17, 7) = 0 OUTPUT
WITH
    ENCRYPTION AS BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
SET
NOCOUNT ON;

DECLARE @Filter VARCHAR(MAX) = 'Artículo',
@IterationCounter INT = 1 WHILE @IterationCounter <= 2 BEGIN DECLARE @CursorDiscountId INT,
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
@CursorItemIds VARCHAR(MAX);

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
    ItemsId
FROM
    dbo.Descuento
WITH
    (NOLOCK)
WHERE
    Estado = 1
    AND TipoDescuento = @Filter
    AND IdArticulo = @ArticleId;

OPEN DiscountCursor;

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
    @CursorItemIds;

WHILE @@FETCH_STATUS = 0 BEGIN
-- Execute the stored procedure
EXEC spValidApplyDiscount @CursorDays,
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
@Discount OUTPUT,
@DiscountPercentage OUTPUT;

-- If a positive discount is evaluated, then break the cursor.
IF @Discount > 0 BEGIN BREAK END
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
    @CursorItemIds;

END CLOSE DiscountCursor;

DEALLOCATE DiscountCursor;

SET
    @IterationCounter = @IterationCounter + 1
SET
    @Filter = 'Articulo' END END GO