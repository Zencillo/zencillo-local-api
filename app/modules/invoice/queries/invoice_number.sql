DECLARE @NumeroFacturaCompleto VARCHAR(MAX), @NuevoNumeroFactura INT,
        @IdResolucion INT, @PrefijoResolucion VARCHAR(MAX), @Resultado INT,
        @FechaExpiracionResolucion DATE, @ResultadoMensaje VARCHAR(MAX);
EXEC dbo.spObtenerNumeroFactura
  @Isla = ?, @IdCompania = ?, @IdCentroVenta = ?, @IdPuntoVenta = ?,
  @CodComprobante = ?, @CodArea = ?, @nCanastilla = ?, @pNumeroFactura = NULL,
  @pPrefijo = NULL, @pIdResolucion = 0, @pNoValidarResolucion = 0,
  @pActualizarResolution = ?, @NumeroFacturaCompleto = @NumeroFacturaCompleto OUTPUT,
  @NuevoNumeroFactura = @NuevoNumeroFactura OUTPUT, @IdResolucion = @IdResolucion OUTPUT,
  @FechaExpiracionResolucion = @FechaExpiracionResolucion OUTPUT,
  @PrefijoResolucion = @PrefijoResolucion OUTPUT, @Resultado = @Resultado OUTPUT,
  @ResultadoMensaje = @ResultadoMensaje OUTPUT;
SELECT @NumeroFacturaCompleto NumeroFacturaCompleto, @NuevoNumeroFactura NuevoNumeroFactura,
       @IdResolucion IdResolucion, @PrefijoResolucion PrefijoResolucion,
       @Resultado Resultado, @ResultadoMensaje ResultadoMensaje,
       @FechaExpiracionResolucion FechaExpiracionResolucion;
