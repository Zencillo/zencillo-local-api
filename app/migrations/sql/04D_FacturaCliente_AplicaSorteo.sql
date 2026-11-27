-- SQL307. Aditivo, idempotente y anterior al SP de lectura (40).
IF COL_LENGTH(N'dbo.FacturaCliente', N'AplicaSorteo') IS NULL
BEGIN
    ALTER TABLE dbo.FacturaCliente
    ADD AplicaSorteo BIT NOT NULL
        CONSTRAINT DF_FacturaCliente_AplicaSorteo DEFAULT (0) WITH VALUES;
END;
