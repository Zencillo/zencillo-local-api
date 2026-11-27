SELECT P.IdConfiguracion, P.MID, P.TID, P.TIC FROM dbo.ConfiguracionPOS AS P
WHERE P.IdCompania = ? AND P.CodigoIsla = ? AND EXISTS (
    SELECT 1 FROM dbo.ConfiguracionInicial AS CI
    WHERE CI.IdCompania = P.IdCompania AND CI.CodigoIsla = P.CodigoIsla AND CI.IdCentroVenta = ?
);
