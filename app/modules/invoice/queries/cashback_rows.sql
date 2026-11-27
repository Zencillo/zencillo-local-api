IF ? IS NULL OR ? IS NULL OR ? IS NULL OR
   (? IS NOT NULL AND NOT EXISTS (
     SELECT 1 FROM dbo.TurnoEmpleado WITH (NOLOCK) WHERE IdTurno = ? AND Isla = ?))
  RAISERROR('Estacion no autorizada.', 16, 1);
ELSE
  EXEC dbo.GetCashBack @pIdTurno = ?, @pIdCashBack = ?, @pNumero = ?, @pTop = ?;
