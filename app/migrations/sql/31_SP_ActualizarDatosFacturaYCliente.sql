IF OBJECT_ID(N'dbo.ActualizarDatosFacturaYCliente', N'P') IS NOT NULL BEGIN DROP
PROCEDURE dbo.ActualizarDatosFacturaYCliente;

END;

GO CREATE
PROCEDURE dbo.ActualizarDatosFacturaYCliente @IdDocumento INT,
@Placa VARCHAR(20),
@IdentificacionCliente VARCHAR(30),
@Kilometraje VARCHAR(15),
@IdentificacionConductor VARCHAR(30),
@NombreCliente VARCHAR(200),
@NombreConductor VARCHAR(200),
@Correo VARCHAR(200),
@IdTurno INT,
@IdVenta INT,
@CodigoIsla INT,
@CodigoCultura INT,
@IdCompania INT,
@IdCentroVenta INT,
@IdPuntoVenta INT,
@IdResolucion INT,
@NumeroFactura VARCHAR(50),
@CodigoComprobante VARCHAR(10),
@VentaCredito BIT,
@IdTransaccion INT,
@RealizoConsolidacion BIT,
@ErrorConsolidacion VARCHAR(200)
WITH
    ENCRYPTION AS BEGIN
SET
NOCOUNT ON;

UPDATE dbo.FacturaCliente
SET
    Placa = @Placa,
    IdentificacionCliente = @IdentificacionCliente,
    Kilometraje = @Kilometraje,
    IdentificacionConductor = @IdentificacionConductor,
    NombreCliente = @NombreCliente,
    NombreConductor = @NombreConductor
WHERE
    IdDocumento = @IdDocumento;

UPDATE dbo.ClienteOffLine
SET
    Correo = @Correo
WHERE
    Identificacion = @IdentificacionCliente;

IF EXISTS (
    SELECT
        1
    FROM
        dbo.ModificacionReimpresion
    WHERE
        IdTurno = @IdTurno
        AND IdVenta = @IdVenta
) BEGIN
UPDATE MR
SET
    CodigoIsla = @CodigoIsla,
    CodigoCultura = @CodigoCultura,
    IdCompania = @IdCompania,
    IdCentroVenta = @IdCentroVenta,
    IdPuntoVenta = @IdPuntoVenta,
    IdResolucion = @IdResolucion,
    NumeroFactura = @NumeroFactura,
    CodigoComprobante = @CodigoComprobante,
    IdentificacionCliente = @IdentificacionCliente,
    Cliente = @NombreCliente,
    Placa = @Placa,
    Kilometraje = @Kilometraje,
    IdentificacionConductor = @IdentificacionConductor,
    NombreConductor = @NombreConductor,
    VentaCredito = @VentaCredito,
    IdTransaccion = @IdTransaccion,
    RealizoConsolidacion = @RealizoConsolidacion,
    ErrorConsolidacion = @ErrorConsolidacion
FROM
    dbo.ModificacionReimpresion AS MR
WHERE
    MR.IdTurno = @IdTurno
    AND MR.IdVenta = @IdVenta;

END ELSE BEGIN
INSERT INTO
    dbo.ModificacionReimpresion (
        IdTurno,
        IdVenta,
        CodigoIsla,
        CodigoCultura,
        IdCompania,
        IdCentroVenta,
        IdPuntoVenta,
        IdResolucion,
        NumeroFactura,
        CodigoComprobante,
        IdentificacionCliente,
        Cliente,
        Placa,
        Kilometraje,
        IdentificacionConductor,
        NombreConductor,
        VentaCredito,
        IdTransaccion,
        RealizoConsolidacion,
        ErrorConsolidacion
    )
VALUES
    (
        @IdTurno,
        @IdVenta,
        @CodigoIsla,
        @CodigoCultura,
        @IdCompania,
        @IdCentroVenta,
        @IdPuntoVenta,
        @IdResolucion,
        @NumeroFactura,
        @CodigoComprobante,
        @IdentificacionCliente,
        @NombreCliente,
        @Placa,
        @Kilometraje,
        @IdentificacionConductor,
        @NombreConductor,
        @VentaCredito,
        @IdTransaccion,
        @RealizoConsolidacion,
        @ErrorConsolidacion
    );

END;

END;

GO