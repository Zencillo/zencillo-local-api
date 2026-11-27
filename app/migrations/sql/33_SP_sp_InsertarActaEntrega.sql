IF OBJECT_ID(N'dbo.sp_InsertarActaEntrega', N'P') IS NOT NULL DROP
PROCEDURE dbo.sp_InsertarActaEntrega;

GO CREATE
PROCEDURE dbo.sp_InsertarActaEntrega @NumeroActaEntrega INT,
@Identificacion VARCHAR(30),
@NombreCliente VARCHAR(200),
@TotalRedimido DECIMAL(18, 7),
@Fecha DATETIME,
@IdTurno INT,
@Detalles XML
WITH ENCRYPTION
AS BEGIN
SET
NOCOUNT ON;

INSERT INTO
    dbo.ActaEntrega (
        NumeroActaEntrega,
        Identificacion,
        NombreCliente,
        TotalRedimido,
        Fecha,
        IdTurno
    )
VALUES
    (
        @NumeroActaEntrega,
        @Identificacion,
        @NombreCliente,
        @TotalRedimido,
        @Fecha,
        @IdTurno
    );

DECLARE @IdGenerado INT;

SET
    @IdGenerado = SCOPE_IDENTITY();

INSERT INTO
    dbo.ActaEntregaDetalle (
        IdActaEntrega,
        Premio,
        Cantidad,
        TotalPuntos,
        TotalValorEmpresa
    )
SELECT
    @IdGenerado,
    Detalle.value ('(Premio/text())[1]', 'VARCHAR(50)'),
    Detalle.value ('(Cantidad/text())[1]', 'DECIMAL(18,7)'),
    Detalle.value ('(TotalPuntos/text())[1]', 'DECIMAL(18,7)'),
    Detalle.value ('(TotalValorEmpresa/text())[1]', 'DECIMAL(18,7)')
FROM
    @Detalles.nodes ('/Detalles/Detalle') AS X (Detalle);

SELECT
    @IdGenerado AS IdActaEntrega;

END;

GO