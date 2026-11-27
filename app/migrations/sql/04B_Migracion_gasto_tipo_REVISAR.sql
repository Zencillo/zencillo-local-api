SET
XACT_ABORT ON;

IF OBJECT_ID(N'dbo.gasto_tipo_backup', N'U') IS NULL
AND OBJECT_ID(N'dbo.gasto_tipo', N'U') IS NOT NULL BEGIN BEGIN TRY BEGIN TRANSACTION;

EXEC sp_rename 'dbo.gasto_tipo',
'gasto_tipo_backup';

CREATE TABLE
    dbo.gasto_tipo (
        idcompania INT NOT NULL,
        idgastotipo INT NOT NULL,
        gastotipo VARCHAR(50) NULL,
        contabilidadcuenta VARCHAR(50) NULL,
        estado BIT NULL,
        fechacreacion DATETIME NULL,
        fechamodificacion DATETIME NULL,
        fechaultimomovimiento DATETIME NULL,
        CONSTRAINT PK_gasto_tipo PRIMARY KEY CLUSTERED (idcompania, idgastotipo)
    );

INSERT INTO
    dbo.gasto_tipo (
        idcompania,
        idgastotipo,
        gastotipo,
        contabilidadcuenta,
        estado,
        fechacreacion,
        fechamodificacion,
        fechaultimomovimiento
    )
SELECT
    idcompania,
    idgastotipo,
    gastotipo,
    contabilidadcuenta,
    estado,
    fechacreacion,
    fechamodificacion,
    fechaultimomovimiento
FROM
    dbo.gasto_tipo_backup;

COMMIT TRANSACTION;

END TRY BEGIN CATCH IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;

DECLARE @MensajeError NVARCHAR(4000);

SET
    @MensajeError = ERROR_MESSAGE();

RAISERROR (@MensajeError, 16, 1);

END CATCH;

END ELSE BEGIN PRINT 'La migración gasto_tipo ya se ejecutó o la tabla original no existe.';

END;