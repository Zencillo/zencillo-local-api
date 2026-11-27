IF NOT EXISTS (SELECT 1 FROM dbo.ConfiguracionGeneral WITH (NOLOCK)
  WHERE IdCompania = ? AND IdCentroVenta = ?)
  RAISERROR('Estacion no autorizada.', 16, 1);
ELSE
  INSERT INTO dbo.AutorizacionExterna
    (IdCompania, Informacion, Process, Mensaje, FechaEjecucion,
     FechaInsercion, Autorizado, Cara)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?);
