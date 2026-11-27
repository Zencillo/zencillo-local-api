SELECT A.IdActaEntrega, A.NumeroActaEntrega, A.Identificacion, A.NombreCliente, A.TotalRedimido, A.Fecha, A.IdTurno FROM dbo.ActaEntrega AS A JOIN dbo.TurnoEmpleado AS T ON T.IdTurno = A.IdTurno WHERE A.IdTurno = ? AND T.Isla = ?
AND EXISTS (SELECT 1 FROM dbo.ConfiguracionInicial
            WHERE IdCompania = ? AND IdCentroVenta = ? AND CodigoIsla = ?);
