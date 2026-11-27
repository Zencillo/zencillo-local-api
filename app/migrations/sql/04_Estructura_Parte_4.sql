-- Generado a partir del script suministrado.
-- Ejecutar respetando el numero del archivo.
SET
NOCOUNT ON;

IF NOT EXISTS (
    SELECT
        *
    FROM
        INFORMATION_SCHEMA.COLUMNS
    WHERE
        COLUMN_NAME = 'TipoPrograma'
        AND TABLE_NAME = 'FacturaClienteFidelizada'
) BEGIN
ALTER TABLE FacturaClienteFidelizada
ADD TipoPrograma INT END IF EXISTS (
    SELECT
        1
    FROM
        sys.key_constraints
    WHERE
        name = 'PK_FacturaClienteFidelizada'
        AND
    TYPE = 'PK'
) BEGIN
ALTER TABLE [dbo].[FacturaClienteFidelizada] DROP CONSTRAINT [PK_FacturaClienteFidelizada];

END IF NOT EXISTS (
    SELECT
        NULL
    FROM
        INFORMATION_SCHEMA.COLUMNS
    WHERE
        TABLE_NAME = 'CheckVentasEstacion'
        AND COLUMN_NAME = 'uid'
) BEGIN
ALTER TABLE CheckVentasEstacion
ADD uid VARCHAR(500) DEFAULT '' END
--ConfiguracionMediaNet
IF OBJECT_ID(N'dbo.ConfiguracionMediaNet', N'U') IS NULL BEGIN
CREATE TABLE
    dbo.ConfiguracionMediaNet (
        id INT IDENTITY(1, 1) NOT NULL,
        ip VARCHAR(50) NOT NULL,
        mascara VARCHAR(50) NOT NULL,
        gateway VARCHAR(50) NOT NULL,
        hostPrinciR1Ip VARCHAR(50) NOT NULL,
        hostPrinciR1Puerto VARCHAR(20) NOT NULL,
        hostAlterR1Ip VARCHAR(50) NOT NULL,
        hostAlterR1Puerto VARCHAR(20) NOT NULL,
        hostPrinciR2Ip VARCHAR(50) NOT NULL,
        hostPrinciR2Puerto VARCHAR(20) NOT NULL,
        hostAlterR2Ip VARCHAR(50) NOT NULL,
        hostAlterR2Puerto VARCHAR(20) NOT NULL,
        puertoEscucha VARCHAR(20) NOT NULL,
        CONSTRAINT PK_ConfiguracionMediaNet PRIMARY KEY CLUSTERED (id)
    );

END;

GO
--columnas adicionales
IF COL_LENGTH('dbo.FacturaCliente', 'facturaProcesada') IS NULL BEGIN
ALTER TABLE dbo.FacturaCliente
ADD facturaProcesada BIT NULL;

END;

GO IF COL_LENGTH(
    'dbo.FacturaClienteFidelizada',
    'IdTipoIdentificacionPromocion'
) IS NULL BEGIN
ALTER TABLE dbo.FacturaClienteFidelizada
ADD IdTipoIdentificacionPromocion VARCHAR(20) NULL;

END;


GO IF COL_LENGTH('dbo.VentasCupo', 'uid') IS NULL
BEGIN
    ALTER TABLE dbo.VentasCupo
    ADD uid VARCHAR(500) NULL;
END;
 
GO IF COL_LENGTH('dbo.VentasCupo', 'valorautorizado') IS NULL 
BEGIN
    ALTER TABLE dbo.VentasCupo
    ADD valorautorizado DECIMAL(17, 7) NULL;

END;

GO IF COL_LENGTH(
    'dbo.FacturaClienteFidelizada',
    'NombreClientePromocion'
) IS NULL BEGIN
ALTER TABLE dbo.FacturaClienteFidelizada
ADD NombreClientePromocion VARCHAR(250) NULL;

END;

GO IF COL_LENGTH(
    'dbo.FacturaClienteFidelizada',
    'IdentificacionPromocion'
) IS NULL BEGIN
ALTER TABLE dbo.FacturaClienteFidelizada
ADD IdentificacionPromocion VARCHAR(50) NULL;

END;

GO IF COL_LENGTH('dbo.FacturaClienteFidelizada', 'IdTipoVehiculo') IS NULL BEGIN
ALTER TABLE dbo.FacturaClienteFidelizada
ADD IdTipoVehiculo INT NULL;

END;

GO IF COL_LENGTH('dbo.FormaPago', 'EnviaDatafono') IS NULL BEGIN
ALTER TABLE dbo.FormaPago
ADD EnviaDatafono INT NOT NULL CONSTRAINT DF_FormaPago_EnviaDatafono DEFAULT 0;

END;

GO IF COL_LENGTH('dbo.FacturaCliente', 'precio_especial') IS NULL BEGIN
ALTER TABLE dbo.FacturaCliente
ADD precio_especial BIT NULL;

END;

GO IF COL_LENGTH('dbo.FacturaCliente', 'es_credito_contingencia') IS NULL BEGIN
ALTER TABLE dbo.FacturaCliente
ADD es_credito_contingencia BIT NULL;

END;

GO IF COL_LENGTH(
    'dbo.CheckVentasEstacion',
    'es_credito_contingencia'
) IS NULL BEGIN
ALTER TABLE dbo.CheckVentasEstacion
ADD es_credito_contingencia BIT NULL;

END;

GO
--forma pago detalle anulado
IF OBJECT_ID(N'dbo.FormaPagoDetalleAnulado', N'U') IS NOT NULL BEGIN IF COL_LENGTH(
    'dbo.FormaPagoDetalleAnulado',
    'IdentificacionRed'
) IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN IdentificacionRed VARCHAR(30) NULL;

IF COL_LENGTH(
    'dbo.FormaPagoDetalleAnulado',
    'CodigoRespuestaActor'
) IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN CodigoRespuestaActor VARCHAR(20) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'MensajeRespuesta') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN MensajeRespuesta VARCHAR(2000) NULL;

IF COL_LENGTH(
    'dbo.FormaPagoDetalleAnulado',
    'NumeroAutorizacion'
) IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN NumeroAutorizacion VARCHAR(20) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'TID') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN TID VARCHAR(30) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'MID') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN MID VARCHAR(30) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'MensajeImpresion') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN MensajeImpresion VARCHAR(2000) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'NombreBanco') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN NombreBanco VARCHAR(150) NULL;

IF COL_LENGTH(
    'dbo.FormaPagoDetalleAnulado',
    'NombreGrupoTarjeta'
) IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN NombreGrupoTarjeta VARCHAR(150) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'ModoLectura') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN ModoLectura VARCHAR(30) NULL;

IF COL_LENGTH(
    'dbo.FormaPagoDetalleAnulado',
    'NombreTarjetaHabiente'
) IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN NombreTarjetaHabiente VARCHAR(150) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'MontoFijo') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN MontoFijo VARCHAR(50) NULL;

IF COL_LENGTH(
    'dbo.FormaPagoDetalleAnulado',
    'IdentificadorAplicacion'
) IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN IdentificadorAplicacion VARCHAR(50) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'AID') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN AID VARCHAR(50) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'TipoCrigtograma') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN TipoCrigtograma VARCHAR(30) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'PIN') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN PIN VARCHAR(50) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'ARQC') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN ARQC VARCHAR(100) NULL;

IF COL_LENGTH(
    'dbo.FormaPagoDetalleAnulado',
    'NumeroTarjetaTruncado'
) IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN NumeroTarjetaTruncado VARCHAR(50) NULL;

IF COL_LENGTH(
    'dbo.FormaPagoDetalleAnulado',
    'NumeroTarjetaEncriptada'
) IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN NumeroTarjetaEncriptada VARCHAR(200) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'Host') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN Host VARCHAR(100) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'HostName') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN HostName VARCHAR(100) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'TipoTarjeta') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN TipoTarjeta VARCHAR(100) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'TipoVenta') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN TipoVenta VARCHAR(50) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'NumeroTarjeta') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN NumeroTarjeta VARCHAR(50) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'LoteAbierto') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN LoteAbierto VARCHAR(20) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'NombreTH') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN NombreTH VARCHAR(150) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'Aprobacion') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN Aprobacion VARCHAR(30) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'IdTerminal') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN IdTerminal VARCHAR(30) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'NumeroReferencia') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN NumeroReferencia VARCHAR(50) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'CodigoReferencia') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN CodigoReferencia VARCHAR(50) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'IdComercio') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN IdComercio VARCHAR(50) NULL;

IF COL_LENGTH(
    'dbo.FormaPagoDetalleAnulado',
    'DiferidoyQuickPayment'
) IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN DiferidoyQuickPayment VARCHAR(50) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'Reservado') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN Reservado VARCHAR(500) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'ArchivoFirma') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN ArchivoFirma VARCHAR(500) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'TVR') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN TVR VARCHAR(100) NULL;

IF COL_LENGTH('dbo.FormaPagoDetalleAnulado', 'TSI') IS NOT NULL
ALTER TABLE dbo.FormaPagoDetalleAnulado
ALTER COLUMN TSI VARCHAR(100) NULL;

END ELSE BEGIN PRINT 'ADVERTENCIA: No existe dbo.FormaPagoDetalleAnulado.';

END;

GO