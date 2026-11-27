-- SQL Server 2008+: procesa una lista de formas de pago en XML y llama
-- dbo.actualizarAcumuladoraFormaPago por cada item.
--
-- XML esperado:
-- <FormasPago>
--   <Item CodFp="01" Valor="1000.0000000" />
--   <Item CodFp="02" Valor="500.5000000" />
-- </FormasPago>

IF OBJECT_ID(N'dbo.sp_ActualizarAcumuladoraFormaPagoBatch', N'P') IS NOT NULL
BEGIN
  DROP PROCEDURE dbo.sp_ActualizarAcumuladoraFormaPagoBatch;
END;

GO

CREATE PROCEDURE dbo.sp_ActualizarAcumuladoraFormaPagoBatch
  @IdTurno INT,
  @FormasPagoXml NVARCHAR(MAX)
WITH ENCRYPTION
AS
BEGIN
  SET NOCOUNT ON;

  IF @FormasPagoXml IS NULL OR LTRIM(RTRIM(@FormasPagoXml)) = N''
  BEGIN
    RETURN;
  END;

  DECLARE @hdoc INT;
  DECLARE @RowNum INT;
  DECLARE @Total INT;
  DECLARE @CodFp VARCHAR(50);
  DECLARE @Valor DECIMAL(17, 7);
  DECLARE @ErrMsg NVARCHAR(4000);
  DECLARE @ErrNum INT;
  DECLARE @ErrLine INT;

  SET @hdoc = 0;

  BEGIN TRY
    EXEC sp_xml_preparedocument @hdoc OUTPUT, @FormasPagoXml;

    IF OBJECT_ID(N'tempdb..#FormasPagoBatch') IS NOT NULL
      DROP TABLE #FormasPagoBatch;

    SELECT
      ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS RowNum,
      CodFp,
      Valor
    INTO #FormasPagoBatch
    FROM OPENXML(@hdoc, N'/FormasPago/Item', 2)
    WITH (
      CodFp VARCHAR(50) N'@CodFp',
      Valor DECIMAL(17, 7) N'@Valor'
    );

    EXEC sp_xml_removedocument @hdoc;
    SET @hdoc = 0;

    SELECT @Total = COUNT(1) FROM #FormasPagoBatch;
    SET @RowNum = 1;

    WHILE @RowNum <= @Total
    BEGIN
      SELECT
        @CodFp = CodFp,
        @Valor = Valor
      FROM #FormasPagoBatch
      WHERE RowNum = @RowNum;

      IF @CodFp IS NOT NULL AND LTRIM(RTRIM(@CodFp)) <> N''
      BEGIN
        EXEC dbo.actualizarAcumuladoraFormaPago
          @IdTurno = @IdTurno,
          @CodFp = @CodFp,
          @Valor = @Valor;
      END;

      SET @RowNum = @RowNum + 1;
    END;

    DROP TABLE #FormasPagoBatch;
  END TRY
  BEGIN CATCH
    IF @hdoc <> 0
    BEGIN
      EXEC sp_xml_removedocument @hdoc;
    END;

    IF OBJECT_ID(N'tempdb..#FormasPagoBatch') IS NOT NULL
      DROP TABLE #FormasPagoBatch;

    SELECT
      @ErrMsg = ERROR_MESSAGE(),
      @ErrNum = ERROR_NUMBER(),
      @ErrLine = ERROR_LINE();

    RAISERROR (
      'sp_ActualizarAcumuladoraFormaPagoBatch | Error %d (Linea %d): %s',
      16,
      1,
      @ErrNum,
      @ErrLine,
      @ErrMsg
    );
  END CATCH;
END;

GO
