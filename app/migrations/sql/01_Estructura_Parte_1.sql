-- Generado a partir del script suministrado.
-- Ejecutar respetando el numero del archivo.
SET NOCOUNT ON;

IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'TypeDataphone' AND TABLE_NAME = 'ConfiguracionPOS')
    BEGIN
        ALTER TABLE ConfiguracionPOS ADD TypeDataphone varchar(30)
    END    

    IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'Correo' AND TABLE_NAME = 'ClientePlacaOffLine')
    BEGIN
        ALTER TABLE ClientePlacaOffLine ADD Correo Varchar(50)
    END
    
    IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'Codigo' AND TABLE_NAME = 'PermisosEmpleado')
    BEGIN
        ALTER TABLE PermisosEmpleado ADD Codigo varchar(30)
    END    

    IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'DigVef' AND TABLE_NAME = 'ClienteOffLine')
    BEGIN
        ALTER TABLE ClienteOffLine ADD DigVef varchar(2) NULL
    END
    
    Update FormaPago set Nombre = REPLACE(Nombre,'á','a')
    Update FormaPago set Nombre = REPLACE(Nombre,'é','e')
    Update FormaPago set Nombre = REPLACE(Nombre,'í','i')
    Update FormaPago set Nombre = REPLACE(Nombre,'ó','o')
    Update FormaPago set Nombre = REPLACE(Nombre,'ú','u')
    
    Update FormaPago set Nombre = REPLACE(Nombre,'Á','A')
    Update FormaPago set Nombre = REPLACE(Nombre,'É','E')
    Update FormaPago set Nombre = REPLACE(Nombre,'Í','I')
    Update FormaPago set Nombre = REPLACE(Nombre,'Ó','O')
    Update FormaPago set Nombre = REPLACE(Nombre,'Ú','U')
    
    Update FormasDePagoPOS set FormaPago = REPLACE(FormaPago,'á','a')
    Update FormasDePagoPOS set FormaPago = REPLACE(FormaPago,'é','e')
    Update FormasDePagoPOS set FormaPago = REPLACE(FormaPago,'í','i')
    Update FormasDePagoPOS set FormaPago = REPLACE(FormaPago,'ó','o')
    Update FormasDePagoPOS set FormaPago = REPLACE(FormaPago,'ú','u')
    
    Update FormasDePagoPOS set FormaPago = REPLACE(FormaPago,'Á','A')
    Update FormasDePagoPOS set FormaPago = REPLACE(FormaPago,'É','E')
    Update FormasDePagoPOS set FormaPago = REPLACE(FormaPago,'Í','I')
    Update FormasDePagoPOS set FormaPago = REPLACE(FormaPago,'Ó','O')
    Update FormasDePagoPOS set FormaPago = REPLACE(FormaPago,'Ú','U')
    
    Update CambioFormaDePagoPOS set FormaPago = REPLACE(FormaPago,'á','a')
    Update CambioFormaDePagoPOS set FormaPago = REPLACE(FormaPago,'é','e')
    Update CambioFormaDePagoPOS set FormaPago = REPLACE(FormaPago,'í','i')
    Update CambioFormaDePagoPOS set FormaPago = REPLACE(FormaPago,'ó','o')
    Update CambioFormaDePagoPOS set FormaPago = REPLACE(FormaPago,'ú','u')
    
    Update CambioFormaDePagoPOS set FormaPago = REPLACE(FormaPago,'Á','A')
    Update CambioFormaDePagoPOS set FormaPago = REPLACE(FormaPago,'É','E')
    Update CambioFormaDePagoPOS set FormaPago = REPLACE(FormaPago,'Í','I')
    Update CambioFormaDePagoPOS set FormaPago = REPLACE(FormaPago,'Ó','O')
    Update CambioFormaDePagoPOS set FormaPago = REPLACE(FormaPago,'Ú','U')
    
    --CREACION DE TALAS CUPO OFFLINE SI NO EXISTEN
    /****** Object:  Table [dbo].[ClienteCupo]    Script Date: 05/28/2021 11:16:02 ******/
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[ClienteCupo]') AND type in (N'U')) BEGIN
        CREATE TABLE [dbo].[ClienteCupo](
        [IdCompania] [numeric](10, 0) NOT NULL,
        [IdClienteCupo] [numeric](10, 0) NOT NULL,
        [IdCliente] [numeric](10, 0) NOT NULL,
        [CupoAsignado] [numeric](28, 8) NOT NULL,
        [CupoDisponible] [numeric](28, 8) NOT NULL,
        [CupoUtilizado] [numeric](28, 8) NOT NULL,
        [SobreCupo] [numeric](28, 8) NULL,
        [SobreCupoDisponible] [numeric](28, 8) NULL,
        [SobreCupoUtilizado] [numeric](28, 8) NULL,
        [PorcentajeCupoDisponible] [numeric](22, 2) NULL,
        [ValorPorcentajeCupoDisponible] [numeric](22, 2) NULL,
        [FechaCreacion] [datetime] NULL,
        [FechaModificacion] [datetime] NULL,
        [FechaUltimoMovimiento] [datetime] NULL,
        [Modificable] [smallint] NULL,
        [IdUsuario] [numeric](10, 0) NULL,
        [Sync] [smallint] NULL,
        [CupoDisponibleAutomotores] [numeric](28, 8) NULL,
        [Auditoria] [bit] NULL,
        [AuditoriaLugarModificacion] [varchar](500) NULL,
        [Identificacion] [varchar](50) NULL,
        [NombreCliente] [varchar](100) NULL,
         CONSTRAINT [PK_ClienteCupo_1] PRIMARY KEY CLUSTERED 
        (
            [IdCompania] ASC,
            [IdClienteCupo] ASC
        )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON, FILLFACTOR = 95) ON [PRIMARY]
        ) ON [PRIMARY]
        
        --CREA IDX
        /****** Object:  Index [IdCompaniaIdCliente]    Script Date: 05/27/2021 12:48:18 ******/
        CREATE UNIQUE NONCLUSTERED INDEX [IdCompaniaIdCliente] ON [dbo].[ClienteCupo] 
        (
            [IdCompania] ASC,
            [IdCliente] ASC
        )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
    END
    
    /****** Object:  Table [dbo].[Automotor]    Script Date: 05/28/2021 11:18:01 ******/
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Automotor]') AND type in (N'U')) BEGIN
            CREATE TABLE [dbo].[Automotor](
            [IdCompania] [int] NOT NULL,
            [IdAutomotor] [int] NOT NULL,
            [IdCliente] [int] NOT NULL,
            [IdCombustible] [int] NULL,
            [IdTipoVehiculo] [int] NULL,
            [IdMarca] [int] NULL,
            [IdModelo] [int] NULL,
            [IdAno] [int] NULL,
            [Placa] [varchar](9) NULL,
            [TarjetaPropiedad] [varchar](50) NULL,
            [Cilindrada] [varchar](10) NULL,
            [TipoMotor] [varchar](20) NULL,
            [NumeroMotor] [varchar](30) NULL,
            [NumeroChasis] [varchar](30) NULL,
            [NumeroRUAT] [varchar](10) NULL,
            [NumeroAsientos] [int] NULL,
            [SincronizadoBsisa] [bit] NULL,
            [BarCode] [varchar](13) NULL,
            [Organizacion] [varchar](50) NULL,
            [OrganizacionDocumento] [varchar](50) NULL,
            [OrganizacionDocumentoFecha] [datetime] NULL,
            [ConsumoDiario] [decimal](18, 2) NULL,
            [CapacidadTanque] [decimal](18, 2) NULL,
            [CantidadDiariaAutorizada] [decimal](18, 2) NULL,
            [Estado] [bit] NULL,
            [PlacaCopia] [int] NULL,
            [FechaCreacion] [datetime] NULL,
            [FechaModificacion] [datetime] NULL,
            [FechaUltimoMovimiento] [datetime] NULL,
            [Modificable] [bit] NULL,
            [IdUsuario] [int] NULL,
            [Sync] [bit] NULL,
            [Galones] [bit] NULL,
            [VAlorRecaudo] [decimal](18, 3) NULL,
            [FechaIniRecaudo] [datetime] NULL,
            [FechaFinRecaudor] [datetime] NULL,
            [AplicaXUnidad] [bit] NULL,
            [Rendimiento] [decimal](11, 2) NULL,
            [CupoXAutomotor] [bit] NULL,
            [MultiplesCombustibles] [bit] NULL,
            [NombreConductor] [varchar](70) NULL,
            [DiasAutorizacion] [int] NULL,
            [IdGrupoAutomotor] [int] NULL,
            [TipoConsumo] [int] NULL,
            [DiaInicial] [int] NULL,
            [DiaFinal] [int] NULL,
            [Combustibles] [varchar](200) NULL,
         CONSTRAINT [PK_Automotor] PRIMARY KEY CLUSTERED 
        (
            [IdCompania] ASC,
            [IdAutomotor] ASC
        )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON, FILLFACTOR = 95) ON [PRIMARY]
        ) ON [PRIMARY]
        
        CREATE UNIQUE NONCLUSTERED INDEX [IDX_IdCompaniaPlaca] ON [dbo].[Automotor] 
        (
            [IdCompania] ASC,
            [Placa] ASC
        )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]    
    END
    
    /****** Object:  Table [dbo].[IdentificadorAutomotor]    Script Date: 05/28/2021 11:19:39 ******/
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[IdentificadorAutomotor]') AND type in (N'U')) BEGIN
        CREATE TABLE [dbo].[IdentificadorAutomotor](
        [IdCompania] [int] NOT NULL,
        [ROM] [varchar](50) NOT NULL,
        [IdAutomotor] [int] NOT NULL,
         CONSTRAINT [PK_IdentificadorAutomotor] PRIMARY KEY CLUSTERED 
        (
            [IdCompania] ASC,
            [ROM] ASC,
            [IdAutomotor] ASC
        )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
        ) ON [PRIMARY]
        
        /****** Object:  Index [IdCompaniaROM]    Script Date: 05/27/2021 12:54:34 ******/
        CREATE UNIQUE NONCLUSTERED INDEX [IdCompaniaROM] ON [dbo].[IdentificadorAutomotor] 
        (
            [IdCompania] ASC,
            [ROM] ASC
        )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
    END
    
    --para almacenar correo del cl
    IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'Correo' AND TABLE_NAME = 'ClienteOffLine')
    BEGIN
        ALTER TABLE ClienteOffLine ADD Correo Varchar(50) NULL
    END
    IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'TipoEmision' AND TABLE_NAME = 'Venta')
    BEGIN
        ALTER TABLE Venta ADD TipoEmision INT NULL
    END
    
    --Crear tabla FormaPagoDetalleCheckIN
    IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'FormaPagoDetalleCheckIN')
    BEGIN
        CREATE TABLE [dbo].[FormaPagoDetalleCheckIN](
        [IdVenta] [int] NOT NULL,
        [IdTurno] [int] NOT NULL,
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
        CONSTRAINT [PK_FormaPagoDetalleCheckIN] PRIMARY KEY CLUSTERED 
        (
        [IdVenta] ASC,
        [IdTurno] ASC,
        [IdFormaPago] ASC
        )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
        ) ON [PRIMARY]
    END
    
    --para los datos del cliente que vienen desde factura.
    IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'Verificado' AND TABLE_NAME = 'ClienteOffline')
    BEGIN
        ALTER TABLE ClienteOffline ADD Verificado INT NULL
    END    
    
    IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'CodTipo' AND TABLE_NAME = 'ClienteOffline')
    BEGIN
        ALTER TABLE ClienteOffline ADD CodTipo Varchar(5) NULL
    END    
    
        
    IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'Manifiesto' AND TABLE_NAME = 'VentasCupo')
    BEGIN
        ALTER TABLE VentasCupo ADD Manifiesto VARCHAR(100) NULL
    END
    
    IF EXISTS (
        SELECT * 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'VentasCupo' AND COLUMN_NAME = 'Manifiesto'
    )
    BEGIN
        ALTER TABLE VentasCupo
        ALTER COLUMN Manifiesto VARCHAR(100)
    END
    
    --tabla para identificar la n cantidad de ventas en una misma transaccion.
    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[FormaPagoDetalleVenta]') AND type in (N'U'))
    BEGIN
        CREATE TABLE [dbo].[FormaPagoDetalleVenta](
            [IdVenta] [int] NOT NULL,
            [IdTurno] [int] NOT NULL,
            [IdVentaAdicional] [int] NOT NULL,
            [Valor] decimal(17,7),
         CONSTRAINT [PK_FormaPagoDetalleVenta] PRIMARY KEY CLUSTERED 
        (
            [IdVenta] ASC,
            [IdTurno] ASC,
            [IdVentaAdicional] ASC
        )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
        ) ON [PRIMARY]
    END
    --tipo venta canastilla no debe tener IdVentaEstacion
    update FacturaCliente set IdVentaEstacion=Null where TipoVenta=3 AND IdVentaEstacion IS NOT NULL
    
    IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'ClienteContrato' AND TABLE_NAME = 'CheckVentasEstacion')
    BEGIN
        ALTER TABLE CheckVentasEstacion ADD ClienteContrato INT NULL
    END    
    
    IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'DatosContrato' AND TABLE_NAME = 'CheckVentasEstacion')
    BEGIN
        ALTER TABLE CheckVentasEstacion ADD DatosContrato Varchar(max)
    END
