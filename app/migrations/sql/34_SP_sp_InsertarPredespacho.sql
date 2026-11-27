IF OBJECT_ID(N'dbo.sp_InsertarPredespacho', N'P') IS NOT NULL DROP
PROCEDURE dbo.sp_InsertarPredespacho;

GO

CREATE PROCEDURE dbo.sp_InsertarPredespacho @nCara INT,
@sIdentificacion VARCHAR(50),
@sNombre NVARCHAR(150),
@xDescuento DECIMAL(17, 7),
@bono_premio BIT,
@sFormaPago VARCHAR(50) = NULL
WITH ENCRYPTION
AS BEGIN
SET
NOCOUNT ON;

DECLARE @idturno INT;

SELECT
    @idturno = ISNULL(
        (
            SELECT
                TOP 1 TE.IdTurno
            FROM
                dbo.CaraIsla AS CI
                INNER JOIN dbo.TurnoEmpleado AS TE ON CI.CodigoIsla = TE.Isla
            WHERE
                TE.Abierto = 1
                AND CI.CodigoCara = @nCara
        ),
        0
    );

UPDATE dbo.predespacho_cliente
SET
    estado = 2,
    fechamodificacion = GETDATE()
WHERE
    cara = @nCara
    AND estado = 0;

INSERT INTO
    dbo.predespacho_cliente (
        cara,
        identificacion,
        nombre,
        estado,
        fechacreacion,
        fechamodificacion,
        idturno,
        descuento,
        bono_premio,
        formaPago
    )
VALUES
    (
        @nCara,
        @sIdentificacion,
        @sNombre,
        0,
        GETDATE(),
        GETDATE(),
        @idturno,
        @xDescuento,
        @bono_premio,
        @sFormaPago
    );

END;

GO