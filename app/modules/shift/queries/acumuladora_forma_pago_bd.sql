SELECT 
        AcumuladoraFormaPago.NombreFormaPago AS NombreFormaPago,
        SUM(AcumuladoraFormaPago.Valor) AS sum_Valor,
        AcumuladoraFormaPago.Codigo AS Codigo
      FROM AcumuladoraFormaPago WITH(NOLOCK)
      WHERE AcumuladoraFormaPago.IdTurno = ?
      GROUP BY AcumuladoraFormaPago.NombreFormaPago, AcumuladoraFormaPago.Codigo
      ORDER BY Codigo ASC
