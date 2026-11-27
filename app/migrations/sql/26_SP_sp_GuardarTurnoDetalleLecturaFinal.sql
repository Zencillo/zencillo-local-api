IF OBJECT_ID(N'dbo.sp_GuardarTurnoDetalleLecturaFinal', N'P') IS NOT NULL BEGIN DROP
PROCEDURE dbo.sp_GuardarTurnoDetalleLecturaFinal;

END;

GO CREATE
PROCEDURE dbo.sp_GuardarTurnoDetalleLecturaFinal @IdTurno INT,
@CodigoManguera INT,
@Lectura DECIMAL(18, 3),
@Precio DECIMAL(18, 7)
WITH
    ENCRYPTION AS BEGIN
SET
NOCOUNT ON;

SET
XACT_ABORT ON;

DECLARE @IdManguera INT;

BEGIN TRY BEGIN TRANSACTION;

SELECT
    @IdManguera = IdManguera
FROM
    dbo.MangueraTanque
WHERE
    CodigoManguera = @CodigoManguera;

IF @IdManguera IS NULL BEGIN RAISERROR (
    'No se encontró una manguera con ese código.',
    16,
    1
);

END;

IF NOT EXISTS (
    SELECT
        1
    FROM
        dbo.TurnoDetalle
    WITH
        (UPDLOCK, HOLDLOCK)
    WHERE
        IdTurno = @IdTurno
        AND IdManguera = @IdManguera
) BEGIN
INSERT INTO
    dbo.TurnoDetalle (
        IdTurno,
        IdManguera,
        LecturaInicial,
        LecturaFinal,
        LecturaDiferencia,
        Precio
    )
VALUES
    (@IdTurno, @IdManguera, @Lectura, 0, 0, @Precio);

END ELSE BEGIN
UPDATE dbo.TurnoDetalle
SET
    LecturaFinal = @Lectura,
    LecturaDiferencia = @Lectura - LecturaInicial,
    Precio = @Precio
WHERE
    IdTurno = @IdTurno
    AND IdManguera = @IdManguera;

END;

COMMIT TRANSACTION;

END TRY BEGIN CATCH IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;

DECLARE @ErrorMessage NVARCHAR(4000);

DECLARE @ErrorSeverity INT;

DECLARE @ErrorState INT;

SELECT
    @ErrorMessage = ERROR_MESSAGE(),
    @ErrorSeverity = ERROR_SEVERITY(),
    @ErrorState = ERROR_STATE();

RAISERROR (@ErrorMessage, @ErrorSeverity, @ErrorState);

END CATCH;

END;

GO