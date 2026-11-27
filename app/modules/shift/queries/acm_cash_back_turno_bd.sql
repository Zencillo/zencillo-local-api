SELECT 
        AcmCashBackTurno.IdTurno AS IdTurno,
        AcmCashBackTurno.CodigoFP AS CodigoFP,
        AcmCashBackTurno.Valor AS Valor,
        AcmCashBackTurno.Fee AS Fee,
        AcmCashBackTurno.Total AS Total,
        FormaPago.IdFormaPago AS IdFormaPago,
        FormaPago.Nombre AS Nombre,
        FormaPago.Codigo AS Codigo
      FROM FormaPago, AcmCashBackTurno
      WHERE FormaPago.Codigo = AcmCashBackTurno.CodigoFP
        AND AcmCashBackTurno.IdTurno = ?
