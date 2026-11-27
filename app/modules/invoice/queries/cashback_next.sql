SELECT ISNULL((SELECT TOP 1 CAST(CBT.numero AS INT) + 1
  FROM dbo.CashBackTurno CBT WITH (NOLOCK)
  INNER JOIN dbo.TurnoEmpleado TE WITH (NOLOCK) ON TE.IdTurno = CBT.IdTurno
  WHERE CBT.IdTurno = ? AND ? IS NOT NULL AND ? IS NOT NULL
    AND ? IS NOT NULL AND TE.Isla = ?
  ORDER BY CAST(CBT.numero AS INT) DESC), 1) AS siguienteNumero;
