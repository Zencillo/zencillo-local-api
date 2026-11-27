INSERT INTO [dbo].[TurnoEmpleado]
      ([FechaZeta],[Isla],[Fecha],[HoraApertura],[HoraCierre],[Abierto],
      [Identificacion],[SincronizoApertura],[SincronizoCierre],
      [NumeroDeTurno],[SincronizoLecturasIniciales],[SincronizoLecturasFinales],
      [SincronizoTotalOperaciones],[Empleado],[ContrasenaEmpleado],[FechaCierre],[XMLApertura])
    VALUES
      (
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        ?,
        (SELECT ISNULL(MAX(NumeroDeTurno),0) + 1 FROM [dbo].[TurnoEmpleado] WHERE Fecha = ? AND Isla = ?),
        ?,
        ?,
        ?,
        ?,
        ?,
        0,
        ?
      )
