DECLARE @Cara int = ?, @Island int = ?, @Company int = ?, @Center int = ?;
IF NOT EXISTS (
    SELECT 1 FROM dbo.CaraIsla AS I
    INNER JOIN dbo.ConfiguracionInicial AS C ON C.CodigoIsla = I.CodigoIsla
    WHERE I.CodigoCara = @Cara AND I.CodigoIsla = @Island
      AND C.IdCompania = @Company AND C.IdCentroVenta = @Center
) OR EXISTS (
    SELECT 1 FROM dbo.CaraIsla WHERE CodigoCara = @Cara AND CodigoIsla <> @Island
)
BEGIN
    RAISERROR ('Cara no autorizada para la estación.', 16, 1);
    RETURN;
END;
EXEC dbo.sp_InsertarPredespacho @nCara = ?, @sIdentificacion = ?, @sNombre = ?,
    @xDescuento = ?, @bono_premio = ?, @sFormaPago = ?;
