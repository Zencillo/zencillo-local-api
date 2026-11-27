-- SQL Server 2008+: sin TRY_CONVERT / IIF / CONCAT / THROW.
-- Contrato: manifiesto + cabeceras + 4 hijos (mismos alias que readQuery).
-- v3: fast path paso 1, #Fc snapshot (N filas), #TieneFpDet, JOIN #Ids en hijos.

IF OBJECT_ID(N'dbo.SP_GET_FACTURAS_CLIENTE_COMPLETE', N'P') IS NOT NULL
BEGIN
  DROP PROCEDURE dbo.SP_GET_FACTURAS_CLIENTE_COMPLETE;
END;

GO

CREATE PROCEDURE dbo.SP_GET_FACTURAS_CLIENTE_COMPLETE
  @MinutosAntes INT = NULL,
  @IdTipoDocumento INT = NULL,
  @TopN INT = NULL,
  @IdFacturaCliente INT = NULL,
  @IdsFacturaCliente NVARCHAR(MAX) = NULL,
  @IdDocumento NVARCHAR(100) = NULL,
  @IdTurno INT = NULL,
  @IdentificacionCliente NVARCHAR(50) = NULL,
  @TipoVentaExcluido NVARCHAR(20) = NULL,
  @CodigoIsla NVARCHAR(20) = NULL,
  @NumeroFactura NVARCHAR(50) = NULL,
  @SoloConvertidos BIT = 0,
  @FromFormaPago BIT = 0,
  @NotaCredito BIT = 0,
  @IsIdDocumento BIT = 0
WITH ENCRYPTION
AS
BEGIN
  SET NOCOUNT ON;

  DECLARE @Limit INT;
  DECLARE @IdsCsv NVARCHAR(MAX);

  SET @Limit = CASE
    WHEN @TopN IS NOT NULL AND @TopN > 0 THEN @TopN
    ELSE 2147483647
  END;

  SET @IdsCsv = CASE
    WHEN @IdsFacturaCliente IS NULL OR LTRIM(RTRIM(@IdsFacturaCliente)) = N'' THEN NULL
    ELSE N',' + REPLACE(LTRIM(RTRIM(@IdsFacturaCliente)), N' ', N'') + N','
  END;

  SELECT 1 AS Id, N'cabeceras' AS Head
  UNION ALL SELECT 2, N'fidelizadas'
  UNION ALL SELECT 3, N'fidelizadasPromociones'
  UNION ALL SELECT 4, N'formaPagoDetalles'
  UNION ALL SELECT 5, N'detalles';

  IF OBJECT_ID(N'tempdb..#Ids') IS NOT NULL
    DROP TABLE #Ids;

  IF OBJECT_ID(N'tempdb..#Fc') IS NOT NULL
    DROP TABLE #Fc;

  IF OBJECT_ID(N'tempdb..#Headers') IS NOT NULL
    DROP TABLE #Headers;

  IF OBJECT_ID(N'tempdb..#TieneFpDet') IS NOT NULL
    DROP TABLE #TieneFpDet;

  CREATE TABLE #Ids (
    IdFacturaCliente INT NOT NULL,
    _OrdenFormaPago INT NULL,
    _OrdenFecha DATETIME NULL
  );

  /*
   * Paso 1: TOP N IdFacturaCliente.
   * Rama A: forma de pago (JOIN ControlProcesosPorVenta + GROUP BY).
   * Rama B: convertidas / NC (EXISTS, sin GROUP BY).
   * Rama C: control turno y resto (solo FacturaCliente).
   */
  IF @FromFormaPago = 1
  BEGIN
    INSERT INTO #Ids (
      IdFacturaCliente,
      _OrdenFormaPago,
      _OrdenFecha
    )
    SELECT TOP (@Limit)
      Q.IdFacturaCliente,
      Q._OrdenFormaPago,
      Q._OrdenFecha
    FROM (
      SELECT
        FC.IdFacturaCliente,
        MAX(CPV.IdVenta) AS _OrdenFormaPago,
        MAX(CASE WHEN 1 = 0 THEN FC.Fecha END) AS _OrdenFecha
      FROM FacturaCliente AS FC WITH (NOLOCK)
      LEFT JOIN FacturaClienteConversion AS CNV WITH (NOLOCK)
        ON CNV.IdFacturaCliente = FC.IdFacturaCliente
      INNER JOIN ControlProcesosPorVenta AS CPV WITH (NOLOCK)
        ON CPV.IdVenta = FC.IdDocumento
      LEFT JOIN NotaCredito AS NC WITH (NOLOCK)
        ON NC.IdFacturaCliente = FC.IdFacturaCliente
      WHERE
        (@IdFacturaCliente IS NULL OR FC.IdFacturaCliente = @IdFacturaCliente)
        AND (
          @IdsCsv IS NULL
          OR CHARINDEX(
            N',' + CAST(FC.IdFacturaCliente AS VARCHAR(20)) + N',',
            @IdsCsv
          ) > 0
        )
        AND (@IdTipoDocumento IS NULL OR FC.IdTipoDocumento = @IdTipoDocumento)
        AND (
          @IdDocumento IS NULL
          OR (
            @IsIdDocumento = 1
            AND FC.IdDocumento LIKE @IdDocumento
            AND FC.IdDocumento = CONVERT(INT, @IdDocumento)
          )
          OR (
            @IsIdDocumento = 0
            AND FC.IdDocumento LIKE @IdDocumento
          )
        )
        AND (@IdTurno IS NULL OR FC.IdTurno = @IdTurno)
        AND (
          @IdentificacionCliente IS NULL
          OR FC.IdentificacionCliente = @IdentificacionCliente
        )
        AND (
          @TipoVentaExcluido IS NULL
          OR FC.TipoVenta <> @TipoVentaExcluido
        )
        AND (@CodigoIsla IS NULL OR FC.CodigoIsla = @CodigoIsla)
        AND (
          @NumeroFactura IS NULL
          OR ISNULL(FC.NumeroFactura, '') = @NumeroFactura
        )
        AND (
          @MinutosAntes IS NULL
          OR @MinutosAntes <= 0
          OR FC.Fecha > DATEADD(MINUTE, -@MinutosAntes, GETDATE())
        )
        AND CPV.CambioFormaPagoVenta = 0
        AND CPV.IdTurno = FC.IdTurno
        AND CPV.TipoVenta <> 2
        AND FC.IdFormaPago <> 6
        AND ISNULL(FC.Anulada, 0) <> 1
        AND ISNULL(FC.panterapago, 0) = 0
        AND (@SoloConvertidos = 0 OR CNV.IdFacturaCliente IS NOT NULL)
        AND (@NotaCredito = 0 OR NC.IdNotaCredito IS NOT NULL)
      GROUP BY FC.IdFacturaCliente
    ) AS Q
    ORDER BY
      Q._OrdenFormaPago DESC,
      Q._OrdenFecha DESC;
  END
  ELSE IF @SoloConvertidos = 1 OR @NotaCredito = 1
  BEGIN
    INSERT INTO #Ids (
      IdFacturaCliente,
      _OrdenFormaPago,
      _OrdenFecha
    )
    SELECT TOP (@Limit)
      FC.IdFacturaCliente,
      CAST(NULL AS INT) AS _OrdenFormaPago,
      FC.Fecha AS _OrdenFecha
    FROM FacturaCliente AS FC WITH (NOLOCK)
    WHERE
      (@IdFacturaCliente IS NULL OR FC.IdFacturaCliente = @IdFacturaCliente)
      AND (
        @IdsCsv IS NULL
        OR CHARINDEX(
          N',' + CAST(FC.IdFacturaCliente AS VARCHAR(20)) + N',',
          @IdsCsv
        ) > 0
      )
      AND (@IdTipoDocumento IS NULL OR FC.IdTipoDocumento = @IdTipoDocumento)
      AND (
        @IdDocumento IS NULL
        OR (
          @IsIdDocumento = 1
          AND FC.IdDocumento LIKE @IdDocumento
          AND FC.IdDocumento = CONVERT(INT, @IdDocumento)
        )
        OR (
          @IsIdDocumento = 0
          AND FC.IdDocumento LIKE @IdDocumento
        )
      )
      AND (@IdTurno IS NULL OR FC.IdTurno = @IdTurno)
      AND (
        @IdentificacionCliente IS NULL
        OR FC.IdentificacionCliente = @IdentificacionCliente
      )
      AND (
        @TipoVentaExcluido IS NULL
        OR FC.TipoVenta <> @TipoVentaExcluido
      )
      AND (@CodigoIsla IS NULL OR FC.CodigoIsla = @CodigoIsla)
      AND (
        @NumeroFactura IS NULL
        OR ISNULL(FC.NumeroFactura, '') = @NumeroFactura
      )
      AND (
        @MinutosAntes IS NULL
        OR @MinutosAntes <= 0
        OR FC.Fecha > DATEADD(MINUTE, -@MinutosAntes, GETDATE())
      )
      AND (
        @SoloConvertidos = 0
        OR EXISTS (
          SELECT 1
          FROM FacturaClienteConversion AS CNV WITH (NOLOCK)
          WHERE CNV.IdFacturaCliente = FC.IdFacturaCliente
        )
      )
      AND (
        @NotaCredito = 0
        OR EXISTS (
          SELECT 1
          FROM NotaCredito AS NC WITH (NOLOCK)
          WHERE NC.IdFacturaCliente = FC.IdFacturaCliente
        )
      )
    ORDER BY FC.Fecha DESC;
  END
  ELSE
  BEGIN
    INSERT INTO #Ids (
      IdFacturaCliente,
      _OrdenFormaPago,
      _OrdenFecha
    )
    SELECT TOP (@Limit)
      FC.IdFacturaCliente,
      CAST(NULL AS INT) AS _OrdenFormaPago,
      FC.Fecha AS _OrdenFecha
    FROM FacturaCliente AS FC WITH (NOLOCK)
    WHERE
      (@IdFacturaCliente IS NULL OR FC.IdFacturaCliente = @IdFacturaCliente)
      AND (
        @IdsCsv IS NULL
        OR CHARINDEX(
          N',' + CAST(FC.IdFacturaCliente AS VARCHAR(20)) + N',',
          @IdsCsv
        ) > 0
      )
      AND (@IdTipoDocumento IS NULL OR FC.IdTipoDocumento = @IdTipoDocumento)
      AND (
        @IdDocumento IS NULL
        OR (
          @IsIdDocumento = 1
          AND FC.IdDocumento LIKE @IdDocumento
          AND FC.IdDocumento = CONVERT(INT, @IdDocumento)
        )
        OR (
          @IsIdDocumento = 0
          AND FC.IdDocumento LIKE @IdDocumento
        )
      )
      AND (@IdTurno IS NULL OR FC.IdTurno = @IdTurno)
      AND (
        @IdentificacionCliente IS NULL
        OR FC.IdentificacionCliente = @IdentificacionCliente
      )
      AND (
        @TipoVentaExcluido IS NULL
        OR FC.TipoVenta <> @TipoVentaExcluido
      )
      AND (@CodigoIsla IS NULL OR FC.CodigoIsla = @CodigoIsla)
      AND (
        @NumeroFactura IS NULL
        OR ISNULL(FC.NumeroFactura, '') = @NumeroFactura
      )
      AND (
        @MinutosAntes IS NULL
        OR @MinutosAntes <= 0
        OR FC.Fecha > DATEADD(MINUTE, -@MinutosAntes, GETDATE())
      )
    ORDER BY FC.Fecha DESC;
  END;

  CREATE CLUSTERED INDEX IX_SP_FacturasClienteComplete_Ids
    ON #Ids (IdFacturaCliente);

  /*
   * Snapshot de las N facturas: evita re-leer FacturaCliente en cada hijo.
   */
  SELECT FC.*
  INTO #Fc
  FROM FacturaCliente AS FC WITH (NOLOCK)
  INNER JOIN #Ids AS I
    ON I.IdFacturaCliente = FC.IdFacturaCliente;

  CREATE CLUSTERED INDEX IX_SP_FacturasClienteComplete_Fc
    ON #Fc (IdFacturaCliente);

  CREATE NONCLUSTERED INDEX IX_SP_FacturasClienteComplete_FcDoc
    ON #Fc (IdDocumento, IdTurno);

  SELECT DISTINCT
    FPD.Idventa AS IdDocumento
  INTO #TieneFpDet
  FROM FormaPagoDetalle AS FPD WITH (NOLOCK)
  INNER JOIN #Fc AS FC
    ON FC.IdDocumento = FPD.Idventa;

  CREATE CLUSTERED INDEX IX_SP_FacturasClienteComplete_TieneFp
    ON #TieneFpDet (IdDocumento);

  SELECT DISTINCT
      ISNULL(NC.IdNotaCredito, 0) AS IdNotaCredito,
      ISNULL(NC.IdFacturaCliente, 0) AS IdFacturaClienteNotaCredito,
      ISNULL(NC.Prefijo, '') AS PrefijoNotaCredito,
      ISNULL(NC.NumeroNotaCredito, '') AS NumeroNotaCredito,
      ISNULL(NC.NumeroAutorizacion, '') AS NumeroAutorizacionNotaCredito,
      ISNULL(CONVERT(VARCHAR(20), NC.Fecha, 120), '') AS FechaNotaCredito,
      FC.IdFacturaCliente AS IdFacturaCliente,
      FC.IdDocumento AS IdDocumento,
      FC.IdTurno AS IdTurno,
      FC.IdTipoDocumento AS IdTipoDocumento,
      FC.CodigoIsla AS CodigoIsla,
      FC.Fecha AS Fecha,
      FC.HoraEntrega AS HoraEntrega,
      FC.IdentificacionCliente AS IdentificacionCliente,
      FC.NombreCliente AS NombreCliente,
      FC.IdResolucion AS IdResolucion,
      ISNULL(FC.PrefijoFactura, '') AS PrefijoFactura,
      ISNULL(FC.NumeroFactura, '') AS NumeroFactura,
      FC.IdFormaPago AS IdFormaPago,
      FC.FormasPago AS FormasPago,
      FC.Placa AS Placa,
      FC.Kilometraje AS Kilometraje,
      FC.TotalIVAS AS TotalIVAS,
      FC.Subtotal AS Subtotal,
      FC.ValorTotalFactura AS ValorTotalFactura,
      FC.PorcentajeDescuento AS PorcentajeDescuento,
      FC.ValorDescuento AS ValorDescuento,
      FC.Propina AS Propina,
      FC.TotalICE AS TotalICE,
      FC.ValorTotalSinSubsidioECU AS ValorTotalSinSubsidioECU,
      FC.AhorroPorSubsidioECU AS AhorroPorSubsidioECU,
      FC.RecaudoSUIC AS RecaudoSUIC,
      FC.TotalaPagar AS TotalaPagar,
      FC.CodigoElectronico AS CodigoElectronico,
      FC.CodigoCara AS CodigoCara,
      FC.CodigoManguera AS CodigoManguera,
      FC.IdVentaEstacion AS IdVentaEstacion,
      FC.SecuenciaVenta AS SecuenciaVenta,
      FC.PuntosAcumulados AS PuntosAcumulados,
      FC.FechaProximaRevicion AS FechaProximaRevicion,
      FC.TipoVenta AS TipoVenta,
      FC.TipoFactura AS TipoFactura,
      FC.TipoEmision AS TipoEmision,
      FC.Facturada AS Facturada,
      ISNULL(FC.Fidelizada, 0) AS Fidelizada,
      CONVERT(INT, FC.AplicaSorteo) AS AplicaSorteo,
      FC.Impresa AS Impresa,
      FC.DatosImpresionFactura AS DatosImpresionFactura,
      FC.IdentificacionConductor AS IdentificacionConductor,
      FC.NombreConductor AS NombreConductor,
      FC.IdentPasaporte AS IdentPasaporte,
      FC.TotalFleet AS TotalFleet,
      FC.ROM AS ROM,
      FC.ModoVenta AS ModoVenta,
      FC.VentaCHIPIslero AS VentaCHIPIslero,
      FC.FacturarConductor AS FacturarConductor,
      FC.BarCodeAutomotor AS BarCodeAutomotor,
      FC.TipoAuth AS TipoAuth,
      FC.tipo_descuento AS TipoDescuento,
      FC.ImpuestoFijo AS ImpuestoFijo,
      ISNULL(FC.VentaConvertida, 0) AS VentaConvertida,
      ISNULL(FC.Anulada, 0) AS VentaAnulada,
      ISNULL(RES_FC.Leyenda1, N'') AS Leyenda1Resolucion,
      ISNULL(RES_FC.Leyenda2, N'') AS Leyenda2Resolucion,
      ISNULL(RES_FC.Leyenda3, N'') AS Leyenda3Resolucion,
      ISNULL(RES_FC.CodigoComprobante, N'') AS CodigoComprobanteResolucion,
      ISNULL(RES_FC.ClaveTecnica, N'') AS ClaveTecnicaResolucion,
      RES_FC.FechaExpiracionResolucion AS FechaExpiracionResolucion,
      ISNULL(RES_CNV.Leyenda1, N'') AS Leyenda1Conversion,
      ISNULL(RES_CNV.Leyenda2, N'') AS Leyenda2Conversion,
      ISNULL(RES_CNV.Leyenda3, N'') AS Leyenda3Conversion,
      ISNULL(RES_CNV.CodigoComprobante, N'') AS CodigoComprobanteConversion,
      ISNULL(RES_CNV.ClaveTecnica, N'') AS ClaveTecnicaConversion,
      RES_CNV.FechaExpiracionResolucion AS FechaExpiracionConversion,
      TN.Empleado,
      ISNULL(FC.panterapago, 0) AS panterapago,
      ISNULL(FC.descripcion, '') AS descripcion,
      ISNULL(FP.FormaPagoFacturaElectronica, '') AS forma_pago_factura_electronica,
      CNV.CodigoElectronico AS CodigoElectronicoConversion,
      CNV.Placa AS PlacaConversion,
      CNV.NombreCliente AS NombreClienteConversion,
      CNV.IdentificacionCliente AS IdentificacionClienteConversion,
      CNV.IdResolucion AS IdResolucionConversion,
      CNV.IdDocumento AS IdDocumentoConversion,
      CNV.IdFacturaClienteConversion AS IdFacturaClienteConversion,
      CNV.Fecha AS FechaConversion,
      CNV.Kilometraje AS KilometrajeConversion,
      CNV.PrefijoFactura AS PrefijoFacturaConversion,
      CNV.NumeroFactura AS NumeroFacturaClienteConversion,
      CNV.TipoFactura AS TipoFacturaConversion,
      CNV.SecuenciaVenta AS SecuenciaVentaConversion,
      FPV.XMLConsolidador,
      CLO.Correo AS CorreoCliente,
      VTA.ValorAutorizado AS ValorAutorizado,
      (VTA.ValorAutorizado - VTA.ValorVenta) AS Cambio,
      ISNULL(VTA.VolumenVenta, 0) AS Volumen,
      ISNULL(FC.Anulada, 0) AS Anulada,
      CPV.IdVenta AS IdVenta,
      CPV.CambioFormaPagoVenta AS CambioFormaPagoVenta,
      CC.CupoDisponible AS CupoDisponible,
      CASE WHEN TFP.IdDocumento IS NOT NULL THEN 1 ELSE 0 END AS TieneDetalleFormaPago
  INTO #Headers
  FROM #Fc AS FC
  LEFT JOIN FormaPago AS FP WITH (NOLOCK)
    ON FP.Codigo = FC.IdFormaPago
  LEFT JOIN FacturaClienteConversion AS CNV WITH (NOLOCK)
    ON CNV.IdFacturaCliente = FC.IdFacturaCliente
  LEFT JOIN Resolucion AS RES_FC WITH (NOLOCK)
    ON RES_FC.IdResolucion = FC.IdResolucion
  LEFT JOIN Resolucion AS RES_CNV WITH (NOLOCK)
    ON RES_CNV.IdResolucion = CNV.IdResolucion
  LEFT JOIN TurnoEmpleado AS TN WITH (NOLOCK)
    ON FC.IdTurno = TN.IdTurno
  LEFT JOIN FormaPagoVenta AS FPV WITH (NOLOCK)
    ON FPV.IdDocumento = FC.IdDocumento
    AND FPV.IdTurno = FC.IdTurno
  LEFT JOIN ClienteOffLine AS CLO WITH (NOLOCK)
    ON CLO.Identificacion = COALESCE(CNV.IdentificacionCliente, FC.IdentificacionCliente)
  LEFT JOIN Venta AS VTA WITH (NOLOCK)
    ON FC.IdVentaEstacion = VTA.CodigoVenta
    AND FC.TipoVenta IN (1, 2)
  LEFT JOIN ClienteCupo AS CC WITH (NOLOCK)
    ON CC.Identificacion = COALESCE(CNV.IdentificacionCliente, FC.IdentificacionCliente)
  LEFT JOIN ControlProcesosPorVenta AS CPV WITH (NOLOCK)
    ON CPV.IdVenta = FC.IdDocumento
  LEFT JOIN NotaCredito AS NC WITH (NOLOCK)
    ON NC.IdFacturaCliente = FC.IdFacturaCliente
  LEFT JOIN #TieneFpDet AS TFP
    ON TFP.IdDocumento = FC.IdDocumento;

  SELECT H.*
  FROM #Headers AS H
  INNER JOIN #Ids AS I
    ON I.IdFacturaCliente = H.IdFacturaCliente
  ORDER BY
    I._OrdenFormaPago DESC,
    I._OrdenFecha DESC;

  SELECT
    F.IdFacturaCliente,
    F.Acumulado,
    F.Redimido,
    F.BalanceActual,
    F.PuntosActivos,
    F.IdentificacionFidelizado,
    F.NombreFidelizado,
    F.Mensaje,
    F.Fecha,
    F.ValorRedimido,
    F.IdTransaccion,
    F.Estado,
    F.ValorAcumulado,
    F.idtipoidentificacion,
    F.TipoPrograma,
    F.IdTipoIdentificacionPromocion,
    F.NombreClientePromocion,
    F.IdentificacionPromocion,
    F.IdTipoVehiculo
  FROM FacturaClienteFidelizada AS F WITH (NOLOCK)
  INNER JOIN #Ids AS I
    ON I.IdFacturaCliente = F.IdFacturaCliente;

  SELECT
    F.IdFacturaCliente,
    F.Acumulado,
    F.Redimido,
    F.BalanceActual,
    F.PuntosActivos,
    F.IdentificacionFidelizado,
    F.NombreFidelizado,
    F.Mensaje,
    F.Fecha,
    F.ValorRedimido,
    F.IdTransaccion,
    F.Estado,
    F.ValorAcumulado,
    F.idtipoidentificacion,
    F.TipoPrograma,
    F.IdTipoIdentificacionPromocion,
    F.NombreClientePromocion,
    F.IdentificacionPromocion,
    F.IdTipoVehiculo
  FROM FacturaClienteFidelizada AS F WITH (NOLOCK)
  INNER JOIN #Ids AS I
    ON I.IdFacturaCliente = F.IdFacturaCliente
  WHERE
    ISNULL(F.IdTipoIdentificacionPromocion, 0) <> 0
    OR ISNULL(LTRIM(RTRIM(F.NombreClientePromocion)), '') <> ''
    OR ISNULL(LTRIM(RTRIM(F.IdentificacionPromocion)), '') <> ''
    OR ISNULL(F.IdTipoVehiculo, 0) <> 0;

  SELECT
    FPD.IdVenta,
    FPD.IdTurno,
    FPD.IdentificacionRed,
    FPD.CodigoRespuestaActor,
    FPD.MensajeRespuesta,
    FPD.SecuencialTransaccion,
    FPD.NumeroLote,
    FPD.HoraTransaccion,
    FPD.FechaTransaccion,
    FPD.NumeroAutorizacion,
    FPD.TID,
    FPD.MID,
    FPD.ValorInteres,
    FPD.MensajeImpresion,
    FPD.CodigoBanco,
    FPD.NombreBanco,
    FPD.NombreGrupoTarjeta,
    FPD.ModoLectura,
    FPD.NombreTarjetaHabiente,
    FPD.MontoFijo,
    FPD.IdentificadorAplicacion,
    FPD.AID,
    FPD.TipoCrigtograma,
    FPD.PIN,
    FPD.ARQC,
    FPD.NumeroTarjetaTruncado,
    FPD.FechaVencimientoTarjeta,
    FPD.NumeroTarjetaEncriptada,
    FPD.Impuesto,
    FPD.BaseConImpuesto,
    FPD.BaseSinImpuesto,
    FPD.MontoImpuesto,
    FPD.MontoTotal,
    FPD.IdFormaPago,
    FPD.Host,
    FPD.HostName,
    FPD.TipoTarjeta,
    FPD.TipoVenta,
    FPD.NumeroTarjeta,
    FPD.LoteAbierto,
    FPD.NombreTH,
    FPD.Aprobacion,
    FPD.IdTerminal,
    FPD.NumeroReferencia,
    FPD.CodigoReferencia,
    FPD.IdComercio,
    FPD.DiferidoyQuickPayment,
    FPD.Reservado,
    FPD.ArchivoFirma,
    FPD.TVR,
    FPD.TSI,
    FPD.Anulada,
    FPD.MultiplesVentas,
    FPD.IdCashBack,
    FC.IdFacturaCliente,
    FC.IdDocumento,
    FC.IdTurno AS IdTurno_Fa,
    FC.IdTipoDocumento,
    FC.CodigoIsla,
    FC.Fecha,
    FC.HoraEntrega,
    FC.IdentificacionCliente,
    FC.NombreCliente,
    FC.IdResolucion,
    FC.PrefijoFactura,
    FC.NumeroFactura,
    FC.IdFormaPago AS IdFormaPago_Fa,
    FC.FormasPago,
    FC.Placa,
    FC.Kilometraje,
    FC.TotalIVAS,
    FC.Subtotal,
    FC.ValorTotalFactura,
    FC.PorcentajeDescuento,
    FC.ValorDescuento,
    FC.Propina,
    FC.TotalICE,
    FC.ValorTotalSinSubsidioECU,
    FC.AhorroPorSubsidioECU,
    FC.RecaudoSUIC,
    FC.TotalaPagar,
    FC.CodigoElectronico,
    FC.CodigoCara,
    FC.CodigoManguera,
    FC.IdVentaEstacion,
    FC.SecuenciaVenta,
    FC.PuntosAcumulados,
    FC.FechaProximaRevicion,
    FC.TipoVenta AS TipoVenta_Fa,
    FC.TipoFactura,
    FC.TipoEmision,
    FC.Facturada,
    FC.Fidelizada,
    FC.Impresa,
    FC.DatosImpresionFactura,
    FC.IdentificacionConductor,
    FC.NombreConductor,
    FC.IdentPasaporte,
    FC.TotalFleet
  FROM FormaPagoDetalle AS FPD WITH (NOLOCK)
  INNER JOIN #Fc AS FC
    ON FC.IdDocumento = FPD.IdVenta
    AND FC.IdTurno = FPD.IdTurno
  ORDER BY FPD.IdVenta DESC;

  SELECT
    D.IdTipoDocumento AS IdTipoDocumento,
    D.IdDocumento AS IdDocumento,
    D.IdFacturaClienteDetalle AS IdFacturaClienteDetalle,
    D.IdArticulo AS IdArticulo,
    D.IdTarifaIVA AS IdTarifaIVA,
    D.Cantidad AS Cantidad,
    D.ValorUnitario AS ValorUnitario,
    ISNULL(D.PorcentajeIVA, 0) AS PorcentajeIVA,
    ISNULL(D.PorcentajeDescuento, 0) AS PorcentajeDescuento,
    D.Subtotal AS Subtotal,
    ISNULL(D.ValorIVA, 0) AS ValorIVA,
    D.Total AS Total,
    D.ValorDescuento AS ValorDescuento,
    D.CodigoICE AS CodigoICE,
    D.PorcentajeICE AS PorcentajeICE,
    D.ValorICE AS ValorICE,
    D.PrecioSinSubsidioECU AS PrecioSinSubsidioECU,
    ART.Presentacion AS Presentacion,
    D.FactorSubsidoECU AS FactorSubsidoECU,
    ART.CodigoArticulo AS CodigoArticulo,
    ART.Articulo AS Articulo,
    ART.IncluyeIVA AS IncluyeIVA,
    ART.imprimir_nombre_corto AS ImprimirNombreContro,
    D.IdFacturaCliente AS IdFacturaCliente,
    ISNULL(ART.ImpuestoValorFijo, 0) AS ImpuestoValorFijo,
    ART.CodigoAlterno,
    ART.NombreCorto AS NombreCorto,
    COMB.IdArticulo AS IdArticuloCombustible
  FROM FacturaClienteDetalle AS D WITH (NOLOCK)
  INNER JOIN #Ids AS I
    ON I.IdFacturaCliente = D.IdFacturaCliente
  LEFT JOIN Articulo AS ART WITH (NOLOCK)
    ON ART.IdArticulo = D.IdArticulo
  LEFT JOIN Combustible AS COMB WITH (NOLOCK)
    ON COMB.CodigoArticulo = ART.CodigoArticulo;
END;
GO
