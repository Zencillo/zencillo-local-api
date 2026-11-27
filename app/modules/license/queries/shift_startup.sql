SELECT
    TE.[IdTurno],
    TE.[FechaZeta],
    TE.[Isla],
    TE.[Fecha] AS FechaTurno,
    TE.[HoraApertura] AS HoraAperturaTurno,
    TE.[HoraCierre] AS HoraCierreTurno,
    TE.[Abierto],
    TE.[Identificacion],
    TE.[SincronizoApertura] AS SincronizoAperturaTurno,
    TE.[SincronizoCierre] AS SincronizoCierreTurno,
    TE.[XMLApertura],
    TE.[XMLCierre],
    TE.[NumeroDeTurno],
    TE.[SincronizoLecturasIniciales] AS SincronizoLecturasInicialesTurno,
    TE.[SincronizoLecturasFinales] AS SincronizoLecturasFinalesTurno,
    TE.[SincronizoTotalOperaciones] AS SincronizoTotalOperacionesTurno,
    TE.[FechaCierre] AS FechaCierreTurno,
    TE.[Empleado] AS EmpleadoTurno,
    TE.[ContrasenaEmpleado] AS ContrasenaEmpleadoTurno,
    ISNULL(PE.[Codigo], '') AS CodigoEmpleado,
    JZ.[IdJornadaZeta],
    JZ.[Fecha] AS FechaJornadaZeta,
    JZ.[HoraApertura] AS HoraAperturaJornadaZeta,
    JZ.[HoraCierre] AS HoraCierreJornadaZeta,
    JZ.[Abierta] AS JornadaZetaAbierta,
    JZ.[SincronizoApertura] AS SincronizoAperturaJornadaZeta,
    JZ.[XMLLecturaInicialTanques],
    JZ.[XMLLecturaFinalTanques],
    JZ.[SincronizoCierre] AS SincronizoCierreJornadaZeta,
    JZ.[SincronizoLecturasIniciales] AS SincronizoLecturasInicialesJornadaZeta,
    JZ.[SincronizoLecturasFinales] AS SincronizoLecturasFinalesJornadaZeta,
    JZ.[SincronizoTotalOperaciones] AS SincronizoTotalOperacionesJornadaZeta,
    JZ.[Empleado] AS EmpleadoJornadaZeta,
    JZ.[ContrasenaEmpleado] AS ContrasenaEmpleadoJornadaZeta,
    JZ.[ManejaConsola],
    JZ.[GuardaVariacion],
    JZ.[CodCapturadorApertura]
FROM [dbo].[TurnoEmpleado] AS TE WITH(NOLOCK)

    LEFT JOIN [dbo].[PermisosEmpleado] AS PE WITH(NOLOCK)
        ON PE.[Identificacion] = TE.[Identificacion]

    LEFT JOIN [dbo].[JornadaZeta] AS JZ WITH(NOLOCK)
        ON JZ.[Fecha] = TE.[FechaZeta]
        AND JZ.[Abierta] = 1
WHERE
    TE.[Isla] = ?
    AND TE.[Abierto] = 1;
