SELECT isnull(FP.IdFormaPago, CFP.Codigo) AS IdFormaPago, CFP.FormaPago, CFP.Codigo, CFP.Activa, FP.EnviaDatafono
      FROM CambioFormaDePagoPOS CFP
      LEFT JOIN FormaPago FP ON CFP.Codigo = FP.Codigo;
