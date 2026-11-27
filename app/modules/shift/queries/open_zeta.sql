INSERT INTO [dbo].[JornadaZeta]
    ([Fecha],[HoraApertura],[Abierta],[SincronizoApertura],
    [SincronizoCierre],[SincronizoLecturasIniciales],[SincronizoLecturasFinales],
    [SincronizoTotalOperaciones],[Empleado],[ContrasenaEmpleado],
    [ManejaConsola],[GuardaVariacion],[CodCapturadorApertura])
    VALUES
    (?, ?, ?, ?,
    ?, ?, ?,
    ?, ?, ?,
    ?, ?, ?);
