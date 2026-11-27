-- Generado a partir del script suministrado.
-- Ejecutar respetando el numero del archivo.
SET NOCOUNT ON;

--creacion de tablas de CashBackTurno en caso de no existir
IF NOT EXISTS(SELECT name FROM sys.sysobjects WHERE Name = N'CashBackTurno' AND xtype = N'U')
BEGIN
    CREATE TABLE [dbo].[CashBackTurno](
    [IdCashBack] [int] IDENTITY(1,1) NOT NULL,
    [IdTurno] [int] NOT NULL,
    [Numero] [int] NOT NULL,
    [CodigoFp] [varchar](5) NOT NULL,
    [Valor] [decimal](17, 7) NOT NULL,
    [Fee] [decimal](17, 7) NOT NULL,
    [Total] [decimal](17, 7) NOT NULL,
    [Fecha] [datetime] NOT NULL,
    [Identificacion] [varchar](50) NOT NULL,
    [Nombre] [varchar](100) NOT NULL,
    [Telefono] [varchar](20) NOT NULL,
    [IncluyeVenta] [bit] NOT NULL,
    [IdDocumento] [int] NULL,
    [Sincronizado] [bit] NOT NULL,
     CONSTRAINT [PK_CashBackTurno] PRIMARY KEY CLUSTERED 
    (
        [IdCashBack] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
    ) ON [PRIMARY]
    
    /****** Object:  Index [IDX_TURNO]    Script Date: 07/18/2022 16:05:26 ******/
    CREATE NONCLUSTERED INDEX [IDX_TURNO] ON [dbo].[CashBackTurno] 
    (
        [IdTurno] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]

    /****** Object:  Index [IDX_TurnoNumero]    Script Date: 07/18/2022 16:05:43 ******/
    CREATE UNIQUE NONCLUSTERED INDEX [IDX_TurnoNumero] ON [dbo].[CashBackTurno] 
    (
        [IdTurno] ASC,
        [Numero] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
END

IF NOT EXISTS(SELECT name FROM sys.sysobjects WHERE Name = N'AcmCashBackTurno' AND xtype = N'U')
BEGIN
    CREATE TABLE [dbo].[AcmCashBackTurno](
    [IdTurno] [int] NOT NULL,
    [CodigoFP] [varchar](5) NOT NULL,
    [Valor] [decimal](17, 7) NOT NULL,
    [Fee] [decimal](17, 7) NOT NULL,
    [Total] [decimal](17, 7) NOT NULL
    ) ON [PRIMARY]
    

    /****** Object:  Index [Idx_IdTurno]    Script Date: 07/18/2022 17:10:50 ******/
    CREATE NONCLUSTERED INDEX [Idx_IdTurno] ON [dbo].[AcmCashBackTurno] 
    (
        [IdTurno] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
END

IF NOT EXISTS( SELECT NULL FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'ClienteOffline' AND COLUMN_NAME = 'Telefono') 
BEGIN 
    ALTER TABLE ClienteOffline ADD Telefono varchar(20)
END

IF NOT EXISTS( SELECT NULL FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FormaPagoDetalle' AND COLUMN_NAME = 'IdCashBack') 
BEGIN 
    ALTER TABLE FormaPagoDetalle ADD IdCashBack int
END
    
--agrega columna de datostransaccion 
IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'DatosTransaccion'  AND TABLE_NAME = 'CHECKVENTASESTACION')
BEGIN
    ALTER TABLE CHECKVENTASESTACION ADD DatosTransaccion varchar(5000) null
END

ALTER TABLE FormaPagoDetalle ALTER COLUMN MensajeRespuesta VARCHAR(2000)

--para almacenar formapafodetalle otros , por ej cashback o otros pagos por diferentes conceptos dif a ventas
IF NOT EXISTS(SELECT name FROM sys.sysobjects WHERE Name = N'FormaPagoDetalleOtros' AND xtype = N'U')
BEGIN
    CREATE TABLE [dbo].[FormaPagoDetalleOtros](
        [Id] [int] NOT NULL IDENTITY (1,1),
        [IdTurno] [int] NOT NULL,
        [IdVenta] [int] NULL,    
        [IdCashBack] [int] NULL,    
        [IdentificacionRed] [varchar](10) NULL,
        [CodigoRespuestaActor] [varchar](20) NULL,
        [MensajeRespuesta] [varchar](500) NULL,
        [SecuencialTransaccion] [int] NULL,
        [NumeroLote] [int] NULL,
        [HoraTransaccion] [int] NULL,
        [FechaTransaccion] [datetime] NULL,
        [NumeroAutorizacion] [varchar](10) NULL,
        [TID] [varchar](20) NULL,
        [MID] [varchar](20) NULL,
        [ValorInteres] [decimal](18, 7) NULL,
        [MensajeImpresion] [varchar](500) NULL,
        [CodigoBanco] [int] NULL,
        [NombreBanco] [varchar](100) NULL,
        [NombreGrupoTarjeta] [varchar](100) NULL,
        [ModoLectura] [varchar](6) NULL,
        [NombreTarjetaHabiente] [varchar](100) NULL,
        [MontoFijo] [varchar](50) NULL,
        [IdentificadorAplicacion] [varchar](20) NULL,
        [AID] [varchar](20) NULL,
        [TipoCrigtograma] [varchar](10) NULL,
        [PIN] [varchar](20) NULL,
        [ARQC] [varchar](20) NULL,
        [NumeroTarjetaTruncado] [varchar](20) NULL,
        [FechaVencimientoTarjeta] [int] NULL,
        [NumeroTarjetaEncriptada] [varchar](20) NULL,
        [Impuesto] [decimal](18, 7) NULL,
        [BaseConImpuesto] [decimal](18, 7) NULL,
        [BaseSinImpuesto] [decimal](18, 7) NULL,
        [MontoImpuesto] [decimal](18, 7) NULL,
        [MontoTotal] [decimal](18, 7) NULL,
        [IdFormaPago] [int] NOT NULL,
        [Host] [varchar](10) NULL,
        [HostName] [varchar](10) NULL,
        [TipoTarjeta] [varchar](10) NULL,
        [TipoVenta] [varchar](10) NULL,
        [NumeroTarjeta] [varchar](20) NULL,
        [LoteAbierto] [varchar](10) NULL,
        [NombreTH] [varchar](50) NULL,
        [Aprobacion] [varchar](10) NULL,
        [IdTerminal] [varchar](10) NULL,
        [NumeroReferencia] [varchar](10) NULL,
        [CodigoReferencia] [varchar](10) NULL,
        [IdComercio] [varchar](20) NULL,
        [DiferidoyQuickPayment] [varchar](10) NULL,
        [Reservado] [varchar](100) NULL,
        [ArchivoFirma] [varchar](100) NULL,
        [TVR] [varchar](100) NULL,
        [TSI] [varchar](100) NULL,
        [Anulada] [bit] NULL,
        [MultiplesVentas] [bit] NULL,
     CONSTRAINT [PK_FormaPagoDetalleOtros] PRIMARY KEY CLUSTERED 
    (
        [Id] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
    ) ON [PRIMARY]
    
    /****** Object:  Index [IDX_IdTurno]    Script Date: 07/18/2022 18:07:31 ******/
    CREATE NONCLUSTERED INDEX [IDX_IdTurno] ON [dbo].[FormaPagoDetalleOtros] 
    (
        [IdTurno] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]

    /****** Object:  Index [Idx_IdTurnoIdCashBack]    Script Date: 07/18/2022 18:07:54 ******/
    CREATE NONCLUSTERED INDEX [Idx_IdTurnoIdCashBack] ON [dbo].[FormaPagoDetalleOtros] 
    (
        [IdTurno] ASC,
        [IdCashBack] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
END

if exists(select 1 from sysobjects
where name = 'spCashBack' 
and type = 'P')
begin
    drop proc spCashBack
end

if exists(select 1 from sysobjects
where name = 'GetCashBack' 
and type = 'P')
begin
    drop proc GetCashBack
end

ALTER TABLE FormaPagoDetalleOtros ALTER COLUMN MensajeRespuesta VARCHAR(2000)

IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'DatosPreciosEDS' AND TABLE_NAME = 'CheckVentasEstacion')
BEGIN
    ALTER TABLE CheckVentasEstacion ADD DatosPreciosEDS Varchar(max)
END    

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ClienteFidelizadoTipo' AND type = 'U')
BEGIN
    CREATE TABLE [dbo].[ClienteFidelizadoTipo](
        [IdClienteFidelizado] [int] NOT NULL,
        [ClienteFidelizado] [varchar](50) NULL,
    CONSTRAINT [PK_ClienteFidelizadoTipo] PRIMARY KEY CLUSTERED (
        [IdClienteFidelizado] ASC
    )WITH (
        PAD_INDEX = OFF, 
        STATISTICS_NORECOMPUTE = OFF, 
        IGNORE_DUP_KEY = OFF, 
        ALLOW_ROW_LOCKS = ON, 
        ALLOW_PAGE_LOCKS = ON
    ) ON [PRIMARY]
    ) ON [PRIMARY]
END

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ArticuloPrecioProgramadoManual' AND type = 'U')
BEGIN
    CREATE TABLE [dbo].[ArticuloPrecioProgramadoManual](
        [IdArticuloPrecioProgramadoManual] [int] IDENTITY(1,1) NOT NULL,
        [CodigoIsla] [int] NOT NULL,
        [IdManguera] [int] NOT NULL,
        [CodigoManguera] [int] NOT NULL,
        [Precio] [decimal](18, 3) NOT NULL,
        [FechaEnviado] [datetime] NOT NULL,
        [Aplicado] [bit] NOT NULL,
        [IdentificacionEmpleado] [varchar](15) NOT NULL,
     CONSTRAINT [PK_ArticuloPrecioProgramadoManual] PRIMARY KEY CLUSTERED 
    (
        [IdArticuloPrecioProgramadoManual] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
    ) ON [PRIMARY]

    ALTER TABLE [dbo].[ArticuloPrecioProgramadoManual] ADD  CONSTRAINT [DF__ArticuloP__Fecha__0308F7B9]  DEFAULT (sysdatetime()) FOR [FechaEnviado]
END

--campos impuesto valor fijo
IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'ImpuestoFijo' AND TABLE_NAME = 'FacturaCliente')
BEGIN
    ALTER TABLE FacturaCliente ADD ImpuestoFijo decimal(17,7)
END

--campos impuesto valor fijo
IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'ImpuestoFijo' AND TABLE_NAME = 'FacturaClienteDetalle')
BEGIN
    ALTER TABLE FacturaClienteDetalle ADD ImpuestoFijo decimal(17,7)
END

--Crea campo ImpuestoValorFijo en la tabla Articulo si no existe.
IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'ImpuestoValorFijo' AND TABLE_NAME = 'Articulo')
BEGIN
    ALTER TABLE Articulo ADD ImpuestoValorFijo decimal(10,4)
END

IF NOT EXISTS(SELECT name FROM sys.sysobjects WHERE Name = N'NotaCredito' AND xtype = N'U')
BEGIN
    CREATE TABLE [dbo].[NotaCredito](
        [IdNotaCredito] [int] IDENTITY(1,1) NOT NULL,
        [IdFacturaCliente] [int] NOT NULL,
        [Prefijo] [varchar](15) NOT NULL,
        [NumeroNotaCredito] [varchar](50) NOT NULL,
        [NumeroAutorizacion] [varchar](49) NOT NULL,
        [Fecha] [datetime] NOT NULL,
     CONSTRAINT [PK_NotaCredito] PRIMARY KEY CLUSTERED 
    (
        [IdNotaCredito] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
    ) ON [PRIMARY]
END

IF NOT EXISTS( SELECT NULL FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'NotaCredito' AND COLUMN_NAME = 'Sincronizada') 
BEGIN 
    ALTER TABLE NotaCredito ADD Sincronizada bit
END

IF NOT EXISTS( SELECT NULL FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'NotaCredito' AND COLUMN_NAME = 'ErrorSincronizacion') 
BEGIN 
    ALTER TABLE NotaCredito ADD ErrorSincronizacion varchar(1000)
END

IF NOT EXISTS( SELECT NULL FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'NotaCredito' AND COLUMN_NAME = 'IdNotaCreditoServidor') 
BEGIN 
    ALTER TABLE NotaCredito ADD IdNotaCreditoServidor int
END

IF NOT EXISTS( SELECT NULL FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FacturaCliente' AND COLUMN_NAME = 'Anulada') 
BEGIN 
    ALTER TABLE FacturaCliente ADD Anulada bit
END

IF NOT EXISTS( SELECT NULL FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FacturaCliente' AND COLUMN_NAME = 'ModoVenta') 
BEGIN 
    ALTER TABLE FacturaCliente ADD ModoVenta int
END

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[TimeToInteger]') AND type IN (N'FN', N'IF', N'TF', N'FS', N'FT'))
BEGIN
    EXEC('CREATE FUNCTION [dbo].[TimeToInteger] (@Hora time)
    RETURNS INT AS
    BEGIN
       RETURN (DATEDIFF(millisecond, ''00:00:00.000'', @Hora) / 10)
    END')
END

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[SplitString]') AND type IN (N'FN', N'IF', N'TF', N'FS', N'FT'))
BEGIN
    EXEC('CREATE FUNCTION dbo.SplitString (@cadena NVARCHAR(MAX), @delimitador CHAR(1))
    RETURNS @resultados TABLE (Elemento NVARCHAR(MAX))
    AS
    BEGIN
       DECLARE @inicio INT, @fin INT
       SET @inicio = 1
       SET @fin = CHARINDEX(@delimitador, @cadena)
    
       WHILE @fin > 0
       BEGIN
          INSERT INTO @resultados (Elemento)
          SELECT SUBSTRING(@cadena, @inicio, @fin - @inicio)
          SET @inicio = @fin + 1
          SET @fin = CHARINDEX(@delimitador, @cadena, @inicio)
       END
    
       INSERT INTO @resultados (Elemento)
       SELECT SUBSTRING(@cadena, @inicio, LEN(@cadena) - @inicio + 1)
    
       RETURN
    END')
END

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'dbo.auditoria_contingencia') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[auditoria_contingencia](
        [id] [int] IDENTITY(1,1) NOT NULL,
        [fecha] [datetime] NOT NULL,
        [proceso] [varchar](50) NOT NULL,
        [usuario] [varchar](50) NOT NULL,
        [descripcion] [varchar](1000) NOT NULL,
     CONSTRAINT [PK_auditoria_contingencia] PRIMARY KEY CLUSTERED 
    (
        [id] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
    ) ON [PRIMARY]


    SET ANSI_PADDING OFF


    ALTER TABLE [dbo].[auditoria_contingencia]  WITH CHECK ADD  CONSTRAINT [FK_auditoria_contingencia_auditoria_contingencia] FOREIGN KEY([id])
    REFERENCES [dbo].[auditoria_contingencia] ([id])

    ALTER TABLE [dbo].[auditoria_contingencia] CHECK CONSTRAINT [FK_auditoria_contingencia_auditoria_contingencia]
END

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'dbo.predespacho_cliente') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[predespacho_cliente](
        [idpredespachocliente] [int] IDENTITY(1,1) NOT NULL,
        [cara] [int] NOT NULL,
        [identificacion] [varchar](50) NOT NULL,
        [nombre] [varchar](250) NOT NULL,
        [estado] [int] NOT NULL,
        [fechacreacion] [datetime] NOT NULL,
        [fechamodificacion] [datetime] NOT NULL,
        [idturno] [int] NOT NULL,
     CONSTRAINT [PK_predespacho_cliente] PRIMARY KEY CLUSTERED 
    (
        [idpredespachocliente] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
    ) ON [PRIMARY]
END

IF NOT EXISTS(SELECT name FROM sys.sysobjects WHERE Name = N'contrato_credito' AND xtype = N'U')
BEGIN
    CREATE TABLE [dbo].[contrato_credito](
        [idcontratocredito] [int] NOT NULL,
        [idcliente] [int] NOT NULL,
        [identificacion] [varchar](50) NOT NULL,
        [cliente] [varchar](250) NOT NULL,
        [fechainicio] [datetime] NOT NULL,
        [fechafin] [datetime] NOT NULL,
        [descripcion] [varchar](2000) NOT NULL,
        [numero] [varchar](50) NOT NULL,
     CONSTRAINT [PK_contrato_credito] PRIMARY KEY CLUSTERED 
    (
        [idcontratocredito] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
    ) ON [PRIMARY]
END

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[FacturaClienteFidelizada]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[FacturaClienteFidelizada](
        [IdFacturaCliente] [int] NOT NULL,
        [Acumulado] [decimal](17, 7) NULL,
        [Redimido] [decimal](17, 7) NULL,
        [BalanceActual] [decimal](17, 7) NULL,
        [PuntosActivos] [decimal](17, 7) NULL,
        [IdentificacionFidelizado] [varchar](50) NULL,
        [NombreFidelizado] [varchar](250) NULL,
        [Mensaje] [varchar](1000) NULL,
        [Fecha] [datetime] NULL,
        [ValorRedimido] [decimal](17, 7) NULL,
        [IdTransaccion] [varchar](50) NULL,
        [Estado] [bit] null,
     CONSTRAINT [PK_FacturaClienteFidelizada] PRIMARY KEY CLUSTERED 
    (
        [IdFacturaCliente] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
    ) ON [PRIMARY]
END
