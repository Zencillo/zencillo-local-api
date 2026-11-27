UPDATE P SET estado = 2, fechamodificacion = SYSDATETIME()
FROM dbo.predespacho_cliente AS P
WHERE P.idpredespachocliente = ? AND EXISTS (
    SELECT 1 FROM dbo.TurnoEmpleado AS T
    JOIN dbo.ConfiguracionInicial AS C ON C.CodigoIsla = T.Isla
    WHERE T.IdTurno = P.idturno AND C.IdCompania = ?
      AND C.IdCentroVenta = ? AND T.Isla = ?
);
