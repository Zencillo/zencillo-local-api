-- El procedimiento se elimina para permitir recrearlo.
IF OBJECT_ID(N'[dbo].[spEvaluateDiscount]', N'P') IS NOT NULL BEGIN DROP
PROCEDURE [dbo].[spEvaluateDiscount];

END GO CREATE
PROCEDURE [dbo].[spEvaluateDiscount] @ArticleId INT,
@PumpFace VARCHAR(MAX),
@HoseId INT,
@Value DECIMAL(17, 7),
@UnitValue DECIMAL(17, 7),
@Quantity DECIMAL(17, 7),
@PaymentMethodId INT,
@Rom VARCHAR(MAX),
@SaleType VARCHAR(MAX),
@ItemCode VARCHAR(MAX),
@LicensePlate VARCHAR(MAX),
@Identification VARCHAR(MAX)
WITH
    ENCRYPTION AS BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
SET
NOCOUNT ON;

DECLARE @Discount DECIMAL(17, 7) = 0,
@DiscountPercentage DECIMAL(17, 7) = 0
SET
    @Identification = REPLACE(@Identification, ' ', '')
    -- Insert statements for procedure here
    BEGIN TRY
    -- General item discount first.
    EXEC spFindDiscountByItem @ArticleId,
    @PumpFace,
    @UnitValue,
    @Quantity,
    @Value,
    @PaymentMethodId,
    @Discount OUTPUT,
    @DiscountPercentage OUTPUT;

IF @Discount > 0 BEGIN PRINT 'DISCOUNT APPLIES FOR ITEM'
SELECT
    ROUND(@Discount, 3) AS Discount,
    @DiscountPercentage AS DiscountPercentage RETURN END
    -- Proceed to verify customer discount
    IF @Identification = '222222222222'
    OR @Identification = '9999999999999'
    OR @Identification = ''
    OR @Identification = '0' BEGIN
SELECT
    ROUND(@Discount, 3) AS Discount,
    @DiscountPercentage AS DiscountPercentage RETURN END
    -- Validate customer discount
    EXEC spSearchDiscountByRom @Identification,
    @PumpFace,
    @UnitValue,
    @Quantity,
    @Value,
    @PaymentMethodId,
    'Cliente',
    @ArticleId,
    @Discount OUTPUT,
    @DiscountPercentage OUTPUT;

IF @Discount > 0 BEGIN PRINT 'DISCOUNT APPLIES FOR CUSTOMER'
SELECT
    ROUND(@Discount, 3) AS Discount,
    @DiscountPercentage AS DiscountPercentage RETURN END
    -- Validate corporate group discount
    DECLARE @CorporateGroupId VARCHAR(MAX) = ISNULL(
        (
            SELECT
                TOP 1 IdGrupoEmpresarial
            FROM
                ClienteOffline
            WITH
                (NOLOCK)
            WHERE
                Identificacion = @Identification
        ),
        ''
    ) IF ISNULL(@CorporateGroupId, '') <> ''
    AND ISNULL(@CorporateGroupId, '') <> '0' BEGIN EXEC spSearchDiscountByRom @CorporateGroupId,
    @PumpFace,
    @UnitValue,
    @Quantity,
    @Value,
    @PaymentMethodId,
    'Grupo Empr',
    @ArticleId,
    @Discount OUTPUT,
    @DiscountPercentage OUTPUT;

IF @Discount > 0 BEGIN PRINT 'DISCOUNT APPLIES FOR CORPORATE GROUP'
SELECT
    ROUND(@Discount, 3) AS Discount,
    @DiscountPercentage AS DiscountPercentage RETURN END EXEC spSearchDiscountByRom @CorporateGroupId,
    @PumpFace,
    @UnitValue,
    @Quantity,
    @Value,
    @PaymentMethodId,
    'Grupo Empresarial',
    @ArticleId,
    @Discount OUTPUT,
    @DiscountPercentage OUTPUT;

IF @Discount > 0 BEGIN PRINT 'DISCOUNT APPLIES FOR CORPORATE GROUP'
SELECT
    ROUND(@Discount, 3) AS Discount,
    @DiscountPercentage AS DiscountPercentage RETURN END END
    -- Discount for license plate, excluding generic plates
    IF @LicensePlate <> ''
    AND @LicensePlate <> 'AAA999'
    AND @LicensePlate <> '0' BEGIN EXEC spSearchDiscountByRom @LicensePlate,
    @PumpFace,
    @UnitValue,
    @Quantity,
    @Value,
    @PaymentMethodId,
    'PLACA',
    @ArticleId,
    @Discount OUTPUT,
    @DiscountPercentage OUTPUT;

IF @Discount > 0 BEGIN PRINT 'DISCOUNT APPLIES FOR LICENSE PLATE'
SELECT
    ROUND(@Discount, 3) AS Discount,
    @DiscountPercentage AS DiscountPercentage RETURN END END
    -- Discount for ROM
    IF @Rom <> ''
    AND @Rom <> '0' BEGIN EXEC spSearchDiscountByRom @Rom,
    @PumpFace,
    @UnitValue,
    @Quantity,
    @Value,
    @PaymentMethodId,
    'ROM/CHIP',
    @ArticleId,
    @Discount OUTPUT,
    @DiscountPercentage OUTPUT;

IF @Discount > 0 BEGIN PRINT 'DISCOUNT APPLIES FOR ROM'
SELECT
    ROUND(@Discount, 3) AS Discount,
    @DiscountPercentage AS DiscountPercentage RETURN END END
SELECT
    ROUND(@Discount, 3) AS Discount,
    @DiscountPercentage AS DiscountPercentage RETURN END TRY BEGIN CATCH PRINT ERROR_MESSAGE()
SELECT
    ROUND(ISNULL(@Discount, 0), 3) AS Discount,
    ISNULL(@DiscountPercentage, 0) AS DiscountPercentage RETURN END CATCH END GO