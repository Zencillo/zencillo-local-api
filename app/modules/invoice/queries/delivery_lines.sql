SELECT D.IdActaEntregaDetalle, D.IdActaEntrega, D.Premio, D.Cantidad, D.TotalPuntos, D.TotalValorEmpresa FROM dbo.ActaEntregaDetalle AS D JOIN dbo.ActaEntrega AS A ON A.IdActaEntrega = D.IdActaEntrega JOIN dbo.TurnoEmpleado AS T ON T.IdTurno = A.IdTurno WHERE D.IdActaEntrega = ? AND T.Isla = ?
AND EXISTS (SELECT 1 FROM dbo.ConfiguracionInicial
            WHERE IdCompania = ? AND IdCentroVenta = ? AND CodigoIsla = ?);
