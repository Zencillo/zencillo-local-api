IF OBJECT_ID(N'dbo.spUpsertResolucion', N'P') IS NOT NULL DROP
PROCEDURE dbo.spUpsertResolucion;

GO CREATE
PROCEDURE dbo.spUpsertResolucion @IdCompania INT,
@IdResolucion INT,
@IdCentroVenta INT,
@IdPuntoVenta INT,
@IdListaTipoResolucion INT,
@NumeroInicial INT,
@NumeroFinal INT,
@FechaAsignacionResolucion DATETIME,
@NumeroResolucion NVARCHAR(100),
@PrefijoFacturacion NVARCHAR(20),
@EstadoResolucion NVARCHAR(20),
@FechaExpiracionResolucion DATETIME,
@UltimoNumeroAsignado INT,
@Leyenda1 NVARCHAR(255),
@Leyenda2 NVARCHAR(255),
@Leyenda3 NVARCHAR(255),
@DiasParaVencimiento INT,
@AlertaCantidad INT,
@DivisionNegocio NVARCHAR(100),
@CodigoComprobante NVARCHAR(100),
@ClaveTecnica NVARCHAR(100)
WITH
    ENCRYPTION AS BEGIN
SET
NOCOUNT ON;

SET
XACT_ABORT ON;

BEGIN TRY BEGIN TRANSACTION;

IF EXISTS (
    SELECT
        1
    FROM
        dbo.Resolucion
    WITH
        (UPDLOCK, HOLDLOCK)
    WHERE
        IdResolucion = @IdResolucion
) BEGIN
UPDATE dbo.Resolucion
SET
    IdCompania = @IdCompania,
    IdCentroVenta = @IdCentroVenta,
    IdPuntoVenta = @IdPuntoVenta,
    IdListaTipoResolucion = @IdListaTipoResolucion,
    NumeroInicial = @NumeroInicial,
    NumeroFinal = @NumeroFinal,
    FechaAsignacionResolucion = @FechaAsignacionResolucion,
    NumeroResolucion = @NumeroResolucion,
    PrefijoFacturacion = @PrefijoFacturacion,
    EstadoResolucion = @EstadoResolucion,
    FechaExpiracionResolucion = @FechaExpiracionResolucion,
    UltimoNumeroAsignado = @UltimoNumeroAsignado,
    Leyenda1 = @Leyenda1,
    Leyenda2 = @Leyenda2,
    Leyenda3 = @Leyenda3,
    DiasParaVencimiento = @DiasParaVencimiento,
    AlertaCantidad = @AlertaCantidad,
    DivisionNegocio = @DivisionNegocio,
    CodigoComprobante = @CodigoComprobante,
    ClaveTecnica = @ClaveTecnica
WHERE
    IdResolucion = @IdResolucion;

END ELSE BEGIN
INSERT INTO
    dbo.Resolucion (
        IdCompania,
        IdResolucion,
        IdCentroVenta,
        IdPuntoVenta,
        IdListaTipoResolucion,
        NumeroInicial,
        NumeroFinal,
        FechaAsignacionResolucion,
        NumeroResolucion,
        PrefijoFacturacion,
        EstadoResolucion,
        FechaExpiracionResolucion,
        UltimoNumeroAsignado,
        Leyenda1,
        Leyenda2,
        Leyenda3,
        DiasParaVencimiento,
        AlertaCantidad,
        DivisionNegocio,
        CodigoComprobante,
        ClaveTecnica
    )
VALUES
    (
        @IdCompania,
        @IdResolucion,
        @IdCentroVenta,
        @IdPuntoVenta,
        @IdListaTipoResolucion,
        @NumeroInicial,
        @NumeroFinal,
        @FechaAsignacionResolucion,
        @NumeroResolucion,
        @PrefijoFacturacion,
        @EstadoResolucion,
        @FechaExpiracionResolucion,
        @UltimoNumeroAsignado,
        @Leyenda1,
        @Leyenda2,
        @Leyenda3,
        @DiasParaVencimiento,
        @AlertaCantidad,
        @DivisionNegocio,
        @CodigoComprobante,
        @ClaveTecnica
    );

END;

COMMIT TRANSACTION;

END TRY BEGIN CATCH IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;

DECLARE @Error NVARCHAR(4000);

SET
    @Error = ERROR_MESSAGE();

RAISERROR (@Error, 16, 1);

END CATCH;

END;

GO