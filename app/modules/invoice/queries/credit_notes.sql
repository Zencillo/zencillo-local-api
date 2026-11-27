SELECT NC.IdNotaCredito, NC.IdFacturaCliente, NC.Prefijo,
       NC.NumeroNotaCredito, NC.NumeroAutorizacion, NC.Fecha
FROM dbo.NotaCredito NC WITH (NOLOCK)
INNER JOIN dbo.FacturaCliente FC WITH (NOLOCK)
  ON FC.IdFacturaCliente = NC.IdFacturaCliente
INNER JOIN dbo.TurnoEmpleado TE WITH (NOLOCK)
  ON TE.IdTurno = FC.IdTurno
WHERE ? IS NOT NULL AND ? IS NOT NULL AND ? IS NOT NULL AND TE.Isla = ?;
