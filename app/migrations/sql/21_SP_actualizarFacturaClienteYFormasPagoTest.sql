IF OBJECT_ID(
    N'dbo.actualizarFacturaClienteYFormasPago',
    N'P'
) IS NOT NULL BEGIN DROP
PROCEDURE dbo.actualizarFacturaClienteYFormasPago;

END;

GO CREATE
PROCEDURE dbo.actualizarFacturaClienteYFormasPago @IDFacturaCliente INT,
@IDFormaPago INT,
@FormasPago NVARCHAR(MAX),
@IdTurno INT,
@CodFp INT,
@Valor DECIMAL(17, 7),
@IdDocumento INT,
@IdCompania INT,
@IdCentroVenta INT,
@CodigoCara INT,
@IdUltimaVenta INT,
@XMLConsolidador NVARCHAR(MAX),
@XMLFactura NVARCHAR(MAX),
@Sincronizada BIT,
@CodigoIsla INT = 10,
@IdVenta INT,
@EsUpdate BIT
WITH
    ENCRYPTION AS BEGIN
SET
NOCOUNT ON;

UPDATE dbo.FacturaCliente
SET
    IdFormaPago = @CodFp,
    FormasPago = @FormasPago
WHERE
    IdFacturaCliente = @IDFacturaCliente;

IF @EsUpdate = 1 BEGIN IF EXISTS (
    SELECT
        1
    FROM
        dbo.FormaPagoVenta
    WITH
        (NOLOCK)
    WHERE
        IdDocumento = @IdDocumento
        AND IdTurno = @IdTurno
) BEGIN
UPDATE dbo.FormaPagoVenta
SET
    IdCompania = @IdCompania,
    IdCentroVenta = @IdCentroVenta,
    CodigoCara = @CodigoCara,
    IdUltimaVenta = @IdUltimaVenta,
    XMLConsolidador = @XMLConsolidador,
    XMLFactura = @XMLFactura,
    Sincronizada = @Sincronizada,
    CodigoIsla = @CodigoIsla
WHERE
    IdDocumento = @IdDocumento
    AND IdTurno = @IdTurno;

END ELSE BEGIN
INSERT INTO
    dbo.FormaPagoVenta (
        IdDocumento,
        IdTurno,
        IdCompania,
        IdCentroVenta,
        CodigoCara,
        IdUltimaVenta,
        XMLConsolidador,
        XMLFactura,
        Sincronizada,
        CodigoIsla
    )
VALUES
    (
        @IdDocumento,
        @IdTurno,
        @IdCompania,
        @IdCentroVenta,
        @CodigoCara,
        @IdUltimaVenta,
        @XMLConsolidador,
        @XMLFactura,
        @Sincronizada,
        @CodigoIsla
    );

END;

END;

UPDATE dbo.ControlProcesosPorVenta
SET
    CambioFormaPagoVenta = 1,
    SincronizaFormasPagoConsolidacion = @Sincronizada,
    SincronizoFormasPagoFacturacion = @Sincronizada
WHERE
    IdVenta = @IdVenta
    AND IdTurno = @IdTurno;

END;

GO