-- Generado a partir del script suministrado.
-- Ejecutar respetando el numero del archivo.
SET NOCOUNT ON;

IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE Name = N'ValorAcumulado' 
    AND Object_ID = Object_ID(N'FacturaClienteFidelizada')
)
BEGIN
    ALTER TABLE [FacturaClienteFidelizada] ADD ValorAcumulado DECIMAL(17,7);
END

IF NOT EXISTS (
    SELECT 1 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'FacturaCliente' 
    AND COLUMN_NAME = 'panterapago'
)
BEGIN
    ALTER TABLE FacturaCliente ADD panterapago BIT;
END

IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE Name = N'idtipoidentificacion' 
    AND Object_ID = Object_ID(N'FacturaClienteFidelizada')
)
BEGIN
    ALTER TABLE [FacturaClienteFidelizada] ADD idtipoidentificacion varchar(20)
END

IF NOT EXISTS (
    SELECT 1 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_SCHEMA = 'dbo' 
    AND TABLE_NAME = 'facturaclientedetalleservicio'
)
BEGIN
    CREATE TABLE [dbo].[facturaclientedetalleservicio](
        [idfacturaclientedetalleservicio] [int] IDENTITY(1,1) NOT NULL,
        [idfacturaclientedetalle] [int] NOT NULL,
        [servicio] [varchar](1500) NOT NULL,
        [transactionId] [varchar](50) NOT NULL,
        [authorizationCode] [varchar](50) NULL,
        [trace] [varchar](50) NULL,
        [pin] [varchar](50) NULL,
        [id_transaccion] [int] NULL,
        [ticket] [varchar](2500) NULL,
     CONSTRAINT [PK_facturaclientedetalleservicio] PRIMARY KEY CLUSTERED 
    (
        [idfacturaclientedetalleservicio] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
    ) ON [PRIMARY]
END

IF NOT EXISTS (
    SELECT * 
    FROM sys.objects 
    WHERE object_id = OBJECT_ID(N'[dbo].[tipo_vehiculo]') 
    AND type = N'U'
) 
BEGIN
    CREATE TABLE [dbo].[tipo_vehiculo](
        [idtipovehiculo] [int] NOT NULL,
        [tipovehiculo] [varchar](50) NOT NULL,
     CONSTRAINT [PK_tipo_vehiculo] PRIMARY KEY CLUSTERED 
    (
        [idtipovehiculo] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
    ) ON [PRIMARY]
END

IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE Name = N'idtipovehiculo' 
    AND Object_ID = Object_ID(N'CheckVentasEstacion')
)
BEGIN
    ALTER TABLE CheckVentasEstacion ADD idtipovehiculo int null
END

--campos impuesto valor fijo
IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'idtipovehiculo' AND TABLE_NAME = 'FacturaCliente')
BEGIN
    ALTER TABLE FacturaCliente ADD idtipovehiculo int null
END

IF NOT EXISTS (
    SELECT 1 
    FROM sys.columns 
    WHERE Name = N'clienteQR' 
    AND Object_ID = Object_ID(N'CheckVentasEstacion')
)
BEGIN
    ALTER TABLE CheckVentasEstacion ADD clienteQR int null
END

--campos impuesto Descripcion
IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'Descripcion' AND TABLE_NAME = 'FacturaCliente')
BEGIN
    ALTER TABLE FacturaCliente ADD Descripcion varchar(2000)
END

--Crea campo facturar_ventas en la tabla TurnoEmpleado si no existe.
IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'facturar_ventas' AND TABLE_NAME = 'TurnoEmpleado')
BEGIN
    ALTER TABLE TurnoEmpleado ADD facturar_ventas bit
END

IF NOT EXISTS( SELECT NULL FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'HistorialPreset' AND COLUMN_NAME = 'Producto') 
BEGIN 
    ALTER TABLE HistorialPreset ADD Producto varchar(50)
END

IF NOT EXISTS(SELECT NULL FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'FormaPago' AND COLUMN_NAME = 'FormaPagoFacturaElectronica') 
BEGIN 
    ALTER TABLE FormaPago ADD FormaPagoFacturaElectronica varchar(100)
END

ALTER TABLE Resolucion ALTER COLUMN Leyenda1 varchar(1000)
ALTER TABLE Resolucion ALTER COLUMN Leyenda2 varchar(1000)
ALTER TABLE Resolucion ALTER COLUMN Leyenda3 varchar(1000)

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'predespacho_cliente' 
      AND COLUMN_NAME = 'descuento'
)
BEGIN
    ALTER TABLE predespacho_cliente ADD descuento decimal(17,7);
END;

IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_NAME = 'predespacho_cliente' 
      AND COLUMN_NAME = 'bono_premio'
)
BEGIN
    ALTER TABLE predespacho_cliente ADD bono_premio bit null
END;

IF NOT EXISTS (
    SELECT NULL
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = 'predespacho_cliente'
      AND COLUMN_NAME = 'formaPago'
)
BEGIN
    ALTER TABLE predespacho_cliente ADD formaPago varchar(50);
END;

--para saber si debe hacer proceso de bono premio
IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'bono_premio' AND TABLE_NAME = 'FacturaCliente')
BEGIN
    ALTER TABLE FacturaCliente ADD bono_premio bit
END

--para saber el tipo de descuento
IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'tipo_descuento' AND TABLE_NAME = 'FacturaCliente')
BEGIN
    ALTER TABLE FacturaCliente ADD tipo_descuento int
END

IF NOT EXISTS(SELECT NULL FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'CheckVentasEstacion' AND COLUMN_NAME = 'acumulapuntos') 
BEGIN 
    ALTER TABLE CheckVentasEstacion ADD acumulapuntos bit
END

--clientes credito que genere venta en efectivo en la eds pero como ticket y no una factura
IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'generaTicketEfectivoEDS' AND TABLE_NAME = 'CheckVentasEstacion')
BEGIN
    ALTER TABLE CheckVentasEstacion ADD generaTicketEfectivoEDS bit
END

IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'aplicaBonoPremio' AND TABLE_NAME = 'CheckVentasEstacion')
BEGIN
    ALTER TABLE CheckVentasEstacion ADD aplicaBonoPremio bit
END

--para saber el tipo de descuento
IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'tipo_descuento' AND TABLE_NAME = 'FacturaCliente')
BEGIN
    ALTER TABLE FacturaCliente ADD tipo_descuento int
END

ALTER TABLE VentasCupo ALTER COLUMN Placa VARCHAR(100)
ALTER TABLE FacturaCliente ALTER COLUMN Placa VARCHAR(100)
ALTER TABLE Venta ALTER COLUMN Placa VARCHAR(100)

IF NOT EXISTS(SELECT NULL FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Descuento' AND COLUMN_NAME = 'montominimo') 
BEGIN 
    ALTER TABLE Descuento ADD montominimo decimal(17,7)
END

--crea nuevo campo tipomonto en la tabla descuento
IF NOT EXISTS(SELECT NULL FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Descuento' AND COLUMN_NAME = 'tipomonto') 
BEGIN 
    ALTER TABLE Descuento ADD tipomonto INT
END

IF NOT EXISTS(SELECT NULL FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Descuento' AND COLUMN_NAME = 'excluyente') 
BEGIN 
    ALTER TABLE Descuento ADD excluyente bit
END

/*Crea la tabla articuloexistencia_pv si no existe.*/
IF NOT EXISTS (SELECT * 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_NAME = 'articuloexistencia_pv')
BEGIN    
    CREATE TABLE [dbo].[articuloexistencia_pv](
        [idarticulo] [int] NOT NULL,
        [idpuntoventa] [int] NOT NULL,
        [saldo] [int] NOT NULL,
     CONSTRAINT [PK_articuloexistencia_pv] PRIMARY KEY CLUSTERED 
    (
        [idarticulo] ASC,
        [idpuntoventa] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
    ) ON [PRIMARY]
END

alter table ConfiguracionInicial alter column DireccionCompania varchar(max)

IF NOT EXISTS ( SELECT 1 FROM sys.tables t INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
                WHERE t.name = 'PlacaIdentificadorOffline' AND s.name = 'dbo')
BEGIN
    CREATE TABLE [dbo].[PlacaIdentificadorOffline](
        [Placa] [varchar](50) NOT NULL,
        [Identificador] [varchar](50) NOT NULL,
     CONSTRAINT [PK_PlacaIdentificadorOffline] PRIMARY KEY CLUSTERED 
    (
        [Placa] ASC,
        [Identificador] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
    ) ON [PRIMARY]
END

IF NOT EXISTS (
    SELECT * 
    FROM sys.columns 
    WHERE Name = N'imprimir_nombre_corto' 
    AND Object_ID = Object_ID(N'dbo.Articulo')
)
BEGIN
    ALTER TABLE Articulo ADD imprimir_nombre_corto bit null
END

IF NOT EXISTS (
    SELECT * 
    FROM sys.columns 
    WHERE Name = N'agregar_nombre_corto_como_detalle_adicional' 
    AND Object_ID = Object_ID(N'dbo.Articulo')
)
BEGIN
    ALTER TABLE Articulo ADD agregar_nombre_corto_como_detalle_adicional bit null
END

IF NOT EXISTS(SELECT name FROM sys.sysobjects WHERE Name = N'gasto_tipo' AND xtype = N'U')
BEGIN
    CREATE TABLE dbo.gasto_tipo (
        idcompania              int NOT NULL,
        idgastotipo             int NOT NULL,
        gastotipo               varchar(50) NULL,
        contabilidadcuenta      varchar(50) NULL,
        estado                    bit NULL,
        fechacreacion           datetime NULL,
        fechamodificacion       datetime NULL,
        fechaultimomovimiento   datetime NULL,
        CONSTRAINT pk_gastotipo PRIMARY KEY CLUSTERED (
            idcompania ASC,
            idgastotipo ASC
        ) WITH (
            PAD_INDEX = OFF,
            STATISTICS_NORECOMPUTE = OFF,
            IGNORE_DUP_KEY = OFF,
            ALLOW_ROW_LOCKS = ON,
            ALLOW_PAGE_LOCKS = ON,
            FILLFACTOR = 95
        ) ON [PRIMARY]
    ) ON [PRIMARY]
END

IF NOT EXISTS(SELECT name FROM sys.sysobjects WHERE Name = N'gasto_turno' AND xtype = N'U')
BEGIN
    CREATE TABLE dbo.gasto_turno (
        idgastoturno    int IDENTITY(1,1) NOT NULL,
        idcompania      int NOT NULL,
        idturno         int NOT NULL,
        idgastotipo     int NOT NULL,
        valor           decimal(17,7) NULL,
        descripcion     varchar(2000) NULL,
        numerofactura   varchar(20) NULL,
        sincronizado   bit NULL,
        CONSTRAINT pk_gasto_turno PRIMARY KEY CLUSTERED (
            idgastoturno ASC
        ) WITH (
            PAD_INDEX = OFF,
            STATISTICS_NORECOMPUTE = OFF,
            IGNORE_DUP_KEY = OFF,
            ALLOW_ROW_LOCKS = ON,
            ALLOW_PAGE_LOCKS = ON,
            FILLFACTOR = 95
        ) ON [PRIMARY]
    ) ON [PRIMARY]
END

IF NOT EXISTS ( SELECT 1
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'integracion_cliente' AND TABLE_SCHEMA = 'dbo' )
BEGIN

    CREATE TABLE [dbo].[integracion_cliente](
        [tipointegracion] [int] NOT NULL,
        [identificacion] [varchar](50) NOT NULL,
        [cliente] [varchar](200) NOT NULL,
        [estado] [bit] NOT NULL,
     CONSTRAINT [PK_integracion_cliente] PRIMARY KEY CLUSTERED 
    (
        [tipointegracion] ASC,
        [identificacion] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON        [PRIMARY]
    ) ON [PRIMARY]
END

ALTER TABLE ConfiguracionPOS ALTER COLUMN LlaveDerecha VARCHAR(500)

IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'manifiesto'  AND TABLE_NAME = 'CHECKVENTASESTACION')
BEGIN
    ALTER TABLE CHECKVENTASESTACION ADD manifiesto varchar(50) null
END

IF NOT EXISTS(SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE COLUMN_NAME = 'manifiesto'  AND TABLE_NAME = 'facturacliente')
BEGIN
    ALTER TABLE facturacliente ADD manifiesto varchar(50) null
END

--add 09 de febrero 2026 wfgd
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='autorizacion_pendiente' AND xtype='U')
BEGIN
    CREATE TABLE [dbo].[autorizacion_pendiente](
        [idautorizacionpendiente] [int] IDENTITY(1,1) NOT NULL,
        [identificacioncliente] [varchar](100) NOT NULL,
        [nombrecliente] [varchar](500) NOT NULL,
        [valorautorizado] [decimal](17, 7) NOT NULL,
        [tipopreset] [int] NOT NULL,
        [formapago] [int] NOT NULL,
        [producto] [varchar](50) NOT NULL,
        [cupoexterno] [int] NOT NULL,
        [placa] [varchar](50) NOT NULL,
        [rom] [varchar](50) NOT NULL,
        [idtransaccion] [varchar](50) NOT NULL,
        [generanotaentrega] [bit] NOT NULL,
        [cara] [int] NOT NULL,
        [fecha] [datetime] NOT NULL,
        [fechaprocesado] [datetime] NULL,
        [pendiente] [bit] NOT NULL,
        [isla] [int] not null,
     CONSTRAINT [PK_autorizacion_pendiente] PRIMARY KEY CLUSTERED 
    (
        [idautorizacionpendiente] ASC
    )WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]
    ) ON [PRIMARY]
END
