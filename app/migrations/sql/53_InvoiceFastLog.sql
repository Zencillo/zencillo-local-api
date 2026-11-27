-- Tabla de trazas internas de InvoiceFast (migracion 301; detalle enriquecido en 302).
-- InvoiceFast acumula pasos en una variable tabla y los vuelca aqui
-- despues de COMMIT o ROLLBACK para que un fallo de venta no borre la traza.
SET
NOCOUNT ON;

IF OBJECT_ID(N'dbo.InvoiceFastLog', N'U') IS NULL BEGIN
CREATE TABLE
    dbo.InvoiceFastLog (
        Id INT IDENTITY(1, 1) NOT NULL,
        Fecha DATETIME NOT NULL,
        Paso VARCHAR(80) NOT NULL,
        Accion VARCHAR(40) NOT NULL,
        IdTurno INT NULL,
        IdVentaEstacion INT NULL,
        nCanastilla INT NULL,
        IdFacturaCliente INT NULL,
        CodigoArticulo VARCHAR(80) NULL,
        CodigoManguera INT NULL,
        Detalle VARCHAR(1000) NULL,
        CONSTRAINT PK_InvoiceFastLog PRIMARY KEY CLUSTERED (Id ASC)
    );

CREATE NONCLUSTERED INDEX IX_InvoiceFastLog_Fecha ON dbo.InvoiceFastLog (Fecha DESC);

CREATE NONCLUSTERED INDEX IX_InvoiceFastLog_IdVentaEstacion ON dbo.InvoiceFastLog (IdVentaEstacion);

END;
