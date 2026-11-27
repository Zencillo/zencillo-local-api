IF ? IS NULL OR ? IS NULL OR ? IS NULL OR NOT EXISTS (
  SELECT 1 FROM dbo.ConfiguracionPOS WITH (NOLOCK) WHERE CodigoIsla = ?)
  RAISERROR('Estacion no autorizada.', 16, 1);
ELSE
  EXEC dbo.sp_ValorCanjeUltimaVenta @CodigoCara = ?;
