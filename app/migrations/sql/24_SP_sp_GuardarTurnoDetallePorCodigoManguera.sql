IF OBJECT_ID(
    N'dbo.sp_GuardarTurnoDetallePorCodigoManguera',
    N'P'
) IS NOT NULL BEGIN DROP
PROCEDURE dbo.sp_GuardarTurnoDetallePorCodigoManguera;

END;

GO CREATE
PROCEDURE dbo.sp_GuardarTurnoDetallePorCodigoManguera @IdTurno INT,
@CodigoManguera INT,
@LecturaValor DECIMAL(18, 2),
@Precio DECIMAL(18, 2)
WITH
    ENCRYPTION AS BEGIN
SET
NOCOUNT ON;

DECLARE @IdManguera INT;

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

RETURN;

END;

IF NOT EXISTS (
    SELECT
        1
    FROM
        dbo.TurnoDetalle
    WITH
        (NOLOCK)
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
    (
        @IdTurno,
        @IdManguera,
        @LecturaValor,
        0,
        0,
        @Precio
    );

END ELSE BEGIN
UPDATE dbo.TurnoDetalle
SET
    LecturaFinal = @LecturaValor,
    LecturaDiferencia = @LecturaValor - LecturaInicial,
    Precio = @Precio
WHERE
    IdTurno = @IdTurno
    AND IdManguera = @IdManguera;

END;

END;

GO