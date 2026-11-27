-- El procedimiento se elimina para permitir recrearlo.
IF OBJECT_ID(N'[dbo].[spValidApplyDiscount]', N'P') IS NOT NULL BEGIN DROP
PROCEDURE [dbo].[spValidApplyDiscount];

END GO CREATE
PROCEDURE [dbo].[spValidApplyDiscount] @DiscountDays VARCHAR(MAX),
@StartDate DATETIME,
@EndDate DATETIME,
@StartHour INT,
@EndHour INT,
@AllHours BIT,
@ConfigDiscountPercentage DECIMAL(17, 7),
@ConfigDiscountAmount DECIMAL(17, 7),
@PumpFace VARCHAR(MAX),
@AppliesPerUnit BIT,
@UnitPrice DECIMAL(17, 7),
@Quantity DECIMAL(17, 7),
@BaseDiscountValue DECIMAL(17, 7),
@PaymentMethodCode INT,
@AllPaymentMethods BIT,
@ExactValue BIT,
@PaymentMethodsIds VARCHAR(MAX),
@DiscountId INT,
--output variables
@DiscountOUT DECIMAL(17, 7) = 0 OUTPUT,
@DiscountPercentageOUT DECIMAL(17, 7) = 0 OUTPUT
WITH
    ENCRYPTION AS BEGIN
    -- SET NOCOUNT ON added to prevent extra result sets from
    -- interfering with SELECT statements.
SET
NOCOUNT ON;

-- Insert statements for procedure here
BEGIN TRY DECLARE @MontoMinimo DECIMAL(17, 0) = 0,
@TipoMonto INT = 0
SELECT
    TOP 1 @MontoMinimo = montominimo,
    @TipoMonto = ISNULL(tipomonto, 0)
FROM
    descuento
WHERE
    iddescuento = @DiscountId
    --add 09 dic 2024 por wfgd solicitud sra narda y don fernando
    --si aplica valor minimo y es por galones/volumen/cantidad se evalua contra rCantidad si rCantidad es  < a rValorMinimo
    --si se cumple esta condicion entonces quiere decir que no cumple y debe omitir la validacion
    IF @MontoMinimo > 0
    AND @TipoMonto = 1
    AND @Quantity < @MontoMinimo BEGIN RETURN END
    --add 09 dic 2024 por wfgd solicitud sra narda y don fernando
    --si aplica valor minimo y es por dinero se evalua contra rCantidad si rCantidad es  < a rValorMinimo
    --si se cumple esta condicion entonces quiere decir que no cumple y debe omitir la validacion
    IF @MontoMinimo > 0
    AND @TipoMonto = 0
    AND @BaseDiscountValue < @MontoMinimo BEGIN RETURN END DECLARE @CurrentDate DATE = GETDATE() DECLARE @CurrentDay VARCHAR(MAX) = LOWER(DATENAME(weekday, @CurrentDate)),
    @CurrentTime INT = dbo.[TimeToInteger] (CONVERT(TIME, GETDATE())),
    @StartInt INT = dbo.DateToInteger (CONVERT(DATE, @StartDate)),
    @EndInt INT = dbo.DateToInteger (CONVERT(DATE, @EndDate)),
    -- If payment method code is not found, defaults to 4 which is cash
    @PaymentMethodId INT = ISNULL(
        (
            SELECT
                TOP 1 IdFormaPago
            FROM
                FormaPago
            WITH
                (nolock)
            WHERE
                Codigo = @PaymentMethodCode
        ),
        4
    )
    --EVALUATE PAYMENT METHOD 
    IF @AllPaymentMethods = 0 BEGIN
    --IF PAYMENT METHOD DOES NOT EXIST FOR SENT PAYMENT METHOD, RETURN AND DO NOT CONTINUE
    IF NOT EXISTS (
        SELECT
            Elemento
        FROM
            dbo.SplitString (@PaymentMethodsIds, ';')
        WHERE
            Elemento = @PaymentMethodId
    ) BEGIN RETURN END END
    -- IF THE DATES ARE NOT WITHIN THE RANGE THEN ALSO RETURNS THE PROCESS
    IF NOT @StartInt <= dbo.DateToInteger (@CurrentDate)
    AND NOT @EndInt >= dbo.DateToInteger (@CurrentDate) BEGIN RETURN END
    --STARTS TO VALIDATE THE DAYS
    DECLARE @element NVARCHAR(MAX),
    @DiscountDaysBit BIT = 0 DECLARE cursorElements CURSOR LOCAL FOR
SELECT
    Elemento
FROM
    dbo.SplitString (@DiscountDays, ',');

OPEN cursorElements;

FETCH NEXT
FROM
    cursorElements INTO @element;

WHILE @@FETCH_STATUS = 0 BEGIN
--VALIDATION OF THE DAYS AUTHORIZED FOR DISCOUNT
IF @element = 'Lu'
AND (
    @CurrentDay = 'lunes'
    OR @CurrentDay = 'monday'
) BEGIN
SET
    @DiscountDaysBit = 1 BREAK END IF @element = 'Ma'
    AND (
        @CurrentDay = 'martes'
        OR @CurrentDay = 'tuesday'
    ) BEGIN
SET
    @DiscountDaysBit = 1 BREAK END IF @element = 'Mi'
    AND (
        @CurrentDay = 'miercoles'
        OR @CurrentDay = 'miércoles'
        OR @CurrentDay = 'wednesday'
    ) BEGIN
SET
    @DiscountDaysBit = 1 BREAK END IF @element = 'Ju'
    AND (
        @CurrentDay = 'jueves'
        OR @CurrentDay = 'thursday'
    ) BEGIN
SET
    @DiscountDaysBit = 1 BREAK END IF @element = 'Vi'
    AND (
        @CurrentDay = 'viernes'
        OR @CurrentDay = 'friday'
    ) BEGIN
SET
    @DiscountDaysBit = 1 BREAK END IF @element = 'Sa'
    AND (
        @CurrentDay = 'sábado'
        OR @CurrentDay = 'sabado'
        OR @CurrentDay = 'saturday'
    ) BEGIN
SET
    @DiscountDaysBit = 1 BREAK END IF @element = 'Do'
    AND (
        @CurrentDay = 'domingo'
        OR @CurrentDay = 'sunday'
    ) BEGIN
SET
    @DiscountDaysBit = 1 BREAK END
FETCH NEXT
FROM
    cursorElements INTO @element;

END CLOSE cursorElements;

DEALLOCATE cursorElements;

--if it does not apply for days then returns
IF @DiscountDaysBit = 0 BEGIN RETURN END
--ROUND QUANTITY TO ZERO DECIMALS IF EXACT VALUE IS REQUIRED
IF @ExactValue = 1 BEGIN
--REDONDEO HACIA ABAJO
SET
    @Quantity = FLOOR(@Quantity) END
    --IF NOT ALL HOURS APPLY, EVALUATE THE HOUR RANGE
    IF @AllHours = 0 BEGIN
    --Normal range validation: e.g., from 06 AM to 10 AM
    IF @StartHour < @EndHour BEGIN IF @CurrentTime >= @StartHour
    AND @CurrentTime <= @EndHour BEGIN
SET
    @DiscountOUT = @ConfigDiscountAmount
SET
    @DiscountPercentageOUT = @ConfigDiscountPercentage END
    --NO APLICA EN LA HORA
    ELSE BEGIN RETURN END END ELSE --Special range validation: e.g., from 06 PM to 06 AM
    BEGIN IF @CurrentTime >= @StartHour
    OR @CurrentTime < @EndHour BEGIN
SET
    @DiscountOUT = @ConfigDiscountAmount
SET
    @DiscountPercentageOUT = @ConfigDiscountPercentage END
    --NO APLICA EN LA HORA
    ELSE BEGIN RETURN END END END ELSE --IF ALL HOURS APPLY
    BEGIN
SET
    @DiscountOUT = @ConfigDiscountAmount
SET
    @DiscountPercentageOUT = @ConfigDiscountPercentage END
    --Set default values if null
SET
    @DiscountOUT = ISNULL(@DiscountOUT, 0)
SET
    @DiscountPercentageOUT = ISNULL(@DiscountPercentageOUT, 0)
    --VALIDATE IF THE DISCOUNT APPLIES PER UNIT
    IF @AppliesPerUnit = 1 BEGIN
    --Calculate discount per item if configured discount is zero and percentage is greater than zero
    IF @DiscountOUT <= 0
    AND @ConfigDiscountPercentage > 0 BEGIN
SET
    @DiscountOUT = @UnitPrice * (@ConfigDiscountPercentage / 100)
SET
    @DiscountOUT = @DiscountOUT * @Quantity END ELSE --Apply discount per quantity
    BEGIN
SET
    @DiscountOUT = @DiscountOUT * @Quantity END END ELSE --Calculate discount based on base value if discount amount is zero or null
    BEGIN IF @DiscountOUT <= 0
    AND @DiscountPercentageOUT > 0 BEGIN
SET
    @DiscountOUT = @BaseDiscountValue * (@DiscountPercentageOUT / 100) END END END TRY BEGIN CATCH
SET
    @DiscountOUT = 0
SET
    @DiscountPercentageOUT = 0 PRINT (ERROR_MESSAGE()) END CATCH END GO