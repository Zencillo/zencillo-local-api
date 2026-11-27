"""Operaciones de puente para migraciones API_ONLY pendientes."""
from app.core.database import SqlDatabase
from app.core.registry import Operation
from app.modules.article.operations import SqlAffectedRows
from app.modules.invoice.operations import FlexibleParameters, SqlRow
from app.schemas import NoParameters, StrictModel
from pydantic import Field


class BagInsert(StrictModel):
    idTurno: int
    codigoBolsa: str = Field(max_length=32)
    valorBillete: float
    valorMoneda: float
    fechaZeta: str = Field(max_length=32)
    horaTurno: str = Field(max_length=32)
    sincronizo: int
    nota: str = Field(max_length=512)


class AuditInsert(StrictModel):
    fecha: str = Field(max_length=32)
    proceso: str = Field(max_length=128)
    usuario: str = Field(max_length=128)
    descripcion: str = Field(max_length=1024)


class DispatchState(StrictModel):
    idPredespachoCliente: int
    estado: int


class PaymentMethodInsert(StrictModel):
    idFormaPago: int
    nombre: str = Field(max_length=128)
    codigo: int


class AccumulatorUpdate(StrictModel):
    idTurno: int
    codFp: str = Field(max_length=32)
    valor: float


class PaymentDetailSale(StrictModel):
    idVenta: int
    idTurno: int
    idVentaAdicional: int
    valor: float


class MedianetConfig(StrictModel):
    ip: str = Field(max_length=64)
    mascara: str = Field(max_length=64)
    gateway: str = Field(max_length=64)
    hostPrinciR1Ip: str = Field(max_length=64)
    hostPrinciR1Puerto: str = Field(max_length=16)
    hostAlterR1Ip: str = Field(max_length=64)
    hostAlterR1Puerto: str = Field(max_length=16)
    hostPrinciR2Ip: str = Field(max_length=64)
    hostPrinciR2Puerto: str = Field(max_length=16)
    hostAlterR2Ip: str = Field(max_length=64)
    hostAlterR2Puerto: str = Field(max_length=16)
    puertoEscucha: str = Field(max_length=16)
    id: int | None = None


class AutomotorKey(StrictModel):
    idCompania: int
    rom: str = Field(min_length=1, max_length=64)


class ShiftIdParam(StrictModel):
    idTurno: int


class IslandCodeParam(StrictModel):
    codigoIsla: int


class ConvertedInvoiceFilter(StrictModel):
    idTurno: int | None = None
    idFacturaCliente: int | None = None


class ShiftInvoiceFilter(StrictModel):
    idTipoDocumento: int
    nMinutosMaximo: int = Field(ge=0, le=10080)
    topN: int = Field(ge=1, le=500)
    idDocumento: str | None = Field(default=None, max_length=64)
    idTurno: int | None = None
    identificacionCliente: str | None = Field(default=None, max_length=64)
    tipoVentaExcluido: str | None = Field(default=None, max_length=32)
    codigoIsla: str | None = Field(default=None, max_length=16)
    numeroFactura: str | None = Field(default=None, max_length=64)


class GeneralConfigKey(StrictModel):
    llave: str = Field(min_length=1, max_length=64, pattern=r'^[A-Za-z][A-Za-z0-9_]*$')
    valor: str | int | float | bool


class InvoicePaymentSimple(StrictModel):
    idFacturaCliente: int
    idFormaPago: int
    formasPago: str = Field(max_length=200)
    idTurno: int
    codFp: str = Field(max_length=32)
    valor: float
    idDocumento: int
    idCompania: int
    idCentroVenta: int
    codigoCara: int
    xmlConsolidador: str = Field(max_length=65536)
    xmlFactura: str = Field(max_length=65536)
    sincronizada: bool
    codigoIsla: int
    esUpdate: bool


_GENERAL_CONFIG_KEYS = frozenset({
    'ManejaZeta', 'ManejaConsola', 'ZetaAutomatica',
    'HoraInicioZetaAutomatica', 'HoraFinZetaAutomatica',
    'VentasPorIslero', 'ValidaFechaUTC', 'UltimaFechaValidadaUTC',
    'NombreClientePredeterminado',
})


def bridge_read_operations(db: SqlDatabase) -> dict[str, Operation]:
    def plates():
        return db.read(
            "SELECT Identificacion, Placa, Identificador, Correo "
            "FROM dbo.ClientePlacaOffLine WITH(NOLOCK)",
            SqlRow,
        )

    def automotor(*, idCompania: int, rom: str):
        return db.read(
            "SELECT IA.ROM, AU.Placa, CC.CupoDisponible, CC.Identificacion, "
            "CC.NombreCliente, AU.Estado, AU.ConsumoDiario "
            "FROM dbo.IdentificadorAutomotor AS IA WITH(NOLOCK) "
            "INNER JOIN dbo.Automotor AS AU WITH(NOLOCK) "
            "ON IA.IdCompania = AU.IdCompania AND IA.IdAutomotor = AU.IdAutomotor "
            "INNER JOIN dbo.ClienteCupo AS CC WITH(NOLOCK) "
            "ON CC.IdCompania = AU.IdCompania AND CC.IdCliente = AU.IdCliente "
            "WHERE IA.IdCompania = ? AND IA.ROM = ?",
            SqlRow,
            parameters=(idCompania, rom),
        )

    def shift_summary(*, idTurno: int):
        return db.read(
            "SELECT "
            "(SELECT ISNULL(SUM(Valor), 0) FROM dbo.AcumuladoraFormaPago WITH(NOLOCK) "
            " WHERE IdTurno = ? AND Codigo = 4) AS TotalEfectivo, "
            "(SELECT ISNULL(SUM(ValorBillete), 0) + ISNULL(SUM(ValorMoneda), 0) "
            " FROM dbo.BolsasTurno WITH(NOLOCK) WHERE IdTurno = ?) AS TotalConsignacion, "
            "(SELECT ISNULL(SUM(AcmCashBackTurno.Total), 0) FROM dbo.FormaPago "
            " INNER JOIN dbo.AcmCashBackTurno ON FormaPago.Codigo = AcmCashBackTurno.CodigoFP "
            " WHERE AcmCashBackTurno.IdTurno = ?) AS TotalCashback, "
            "(SELECT ISNULL(SUM(gasto_turno.valor), 0) FROM dbo.gasto_turno "
            " WHERE gasto_turno.IdTurno = ?) AS TotalGasto, "
            "(SELECT ISNULL((SELECT TOP 1 CAST(CodigoBolsa AS INT) + 1 "
            " FROM dbo.BolsasTurno WITH(NOLOCK) WHERE IdTurno = ? "
            " ORDER BY CAST(CodigoBolsa AS INT) DESC), 1)) AS SiguienteCodigoBolsa",
            SqlRow,
            parameters=(idTurno, idTurno, idTurno, idTurno, idTurno),
        )

    def expenses():
        return db.read(
            "SELECT idgastoturno, gasto_tipo.gastotipo AS gasto, "
            "gasto_turno.idcompania, idturno, gasto_turno.idgastotipo, "
            "valor, descripcion, numerofactura, sincronizado "
            "FROM dbo.gasto_turno "
            "INNER JOIN dbo.gasto_tipo "
            "ON gasto_tipo.idgastotipo = gasto_turno.idgastotipo",
            SqlRow,
        )

    def audits():
        return db.read(
            "SELECT id, fecha, proceso, usuario, descripcion "
            "FROM dbo.AuditoriaContingencia WITH(NOLOCK)",
            SqlRow,
        )

    def prices_by_island(*, codigoIsla: int):
        return db.read(
            "SELECT IdArticuloPrecioProgramado, CodigoIsla, IdManguera, "
            "CodigoManguera, Precio1, Precio2, Precio3, Precio4, Fecha, "
            "HoraInicio, HoraFin, Aplicado "
            "FROM dbo.ArticuloPrecioProgramado WITH(NOLOCK) "
            "WHERE CodigoIsla = ?",
            SqlRow,
            parameters=(str(codigoIsla),),
        )

    def converted(**values):
        clauses = []
        params = []
        if values.get('idTurno') is not None:
            clauses.append('FacturaCliente.IdTurno = ?')
            params.append(values['idTurno'])
        if values.get('idFacturaCliente') is not None:
            clauses.append('FacturaCliente.IdFacturaCliente = ?')
            params.append(values['idFacturaCliente'])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ''
        return db.read(
            "SELECT TOP 50 "
            "FacturaCliente.IdFacturaCliente AS IdFacturaCliente, "
            "FacturaCliente.IdTipoDocumento AS IdTipoDocumento, "
            "FacturaClienteConversion.IdDocumento AS IdDocumento, "
            "FacturaClienteConversion.IdResolucion AS IdResolucion, "
            "FacturaCliente.IdFormaPago AS IdFormaPago, "
            "FacturaClienteConversion.TipoFactura AS TipoFactura, "
            "FacturaClienteConversion.NumeroFactura AS NumeroFactura, "
            "FacturaClienteConversion.PrefijoFactura AS PrefijoFactura, "
            "FacturaClienteConversion.Fecha AS Fecha, "
            "FacturaCliente.ValorTotalFactura AS ValorTotalFactura, "
            "FacturaCliente.Subtotal AS Subtotal, "
            "FacturaCliente.PorcentajeDescuento AS PorcentajeDescuento, "
            "FacturaCliente.ValorDescuento AS ValorDescuento, "
            "FacturaCliente.TotalIVAS AS TotalIVAS, "
            "FacturaCliente.IdTurno AS IdTurno, "
            "FacturaCliente.HoraEntrega AS HoraEntrega, "
            "FacturaClienteConversion.CodigoElectronico AS CodigoElectronico, "
            "FacturaCliente.Propina AS Propina, "
            "FacturaCliente.TotalICE AS TotalICE, "
            "FacturaClienteConversion.Placa AS Placa, "
            "FacturaClienteConversion.IdentificacionCliente AS IdentificacionCliente, "
            "FacturaClienteConversion.NombreCliente AS NombreCliente, "
            "FacturaCliente.TipoEmision AS TipoEmision, "
            "FacturaCliente.CodigoCara AS CodigoCara, "
            "FacturaCliente.PuntosAcumulados AS PuntosAcumulados, "
            "FacturaCliente.TotalaPagar AS TotalaPagar, "
            "FacturaClienteConversion.SecuenciaVenta AS SecuenciaVenta, "
            "FacturaCliente.Facturada AS Facturada, "
            "FacturaCliente.Fidelizada AS Fidelizada, "
            "FacturaCliente.FormasPago AS FormasPago, "
            "FacturaClienteConversion.TipoVenta AS TipoVenta, "
            "FacturaCliente.CodigoIsla AS CodigoIsla, "
            "FacturaCliente.DatosImpresionFactura AS DatosImpresionFactura, "
            "FacturaCliente.FechaProximaRevicion, "
            "FacturaClienteConversion.Kilometraje, "
            "FacturaCliente.IdentificacionConductor, "
            "FacturaCliente.NombreConductor, "
            "FacturaCliente.VentaConvertida "
            "FROM dbo.FacturaCliente WITH(NOLOCK) "
            "INNER JOIN dbo.FacturaClienteConversion WITH(NOLOCK) "
            "ON FacturaClienteConversion.IdFacturaCliente = FacturaCliente.IdFacturaCliente "
            f"{where} ORDER BY Fecha DESC",
            SqlRow,
            parameters=tuple(params),
        )

    def shift_invoices(**values):
        top = int(values['topN'])
        minutes = int(values['nMinutosMaximo'])
        clauses = [
            'FacturaCliente.IdTipoDocumento = ?',
            '((? = 0) OR (FacturaCliente.Fecha > DATEADD(MINUTE, -?, GETDATE())))',
        ]
        params = [values['idTipoDocumento'], minutes, minutes]
        optional = (
            ('idDocumento', "FacturaCliente.IdDocumento LIKE ?", True),
            ('idTurno', 'FacturaCliente.IdTurno = ?', False),
            ('identificacionCliente',
             "FacturaCliente.IdentificacionCliente = ?", True),
            ('tipoVentaExcluido', "FacturaCliente.TipoVenta <> ?", True),
            ('codigoIsla', "FacturaCliente.CodigoIsla = ?", True),
            ('numeroFactura',
             "ISNULL(FacturaCliente.NumeroFactura,'') = ?", True),
        )
        for key, clause, _ in optional:
            value = values.get(key)
            if value is None or value == '':
                continue
            clauses.append(clause)
            params.append(value)
        where = ' AND '.join(clauses)
        return db.read(
            f"SELECT DISTINCT TOP ({top}) "
            "FacturaCliente.IdFacturaCliente AS IdFacturaCliente, "
            "FacturaCliente.IdTipoDocumento AS IdTipoDocumento, "
            "FacturaCliente.IdDocumento AS IdDocumento, "
            "FacturaCliente.IdResolucion AS IdResolucion, "
            "FacturaCliente.IdFormaPago AS IdFormaPago, "
            "FacturaCliente.TipoFactura AS TipoFactura, "
            "ISNULL(FacturaCliente.NumeroFactura,'') AS NumeroFactura, "
            "ISNULL(FacturaCliente.PrefijoFactura,'') AS PrefijoFactura, "
            "FacturaCliente.Fecha AS Fecha, "
            "FacturaCliente.ValorTotalFactura AS ValorTotalFactura, "
            "FacturaCliente.Subtotal AS Subtotal, "
            "FacturaCliente.PorcentajeDescuento AS PorcentajeDescuento, "
            "FacturaCliente.ValorDescuento AS ValorDescuento, "
            "FacturaCliente.TotalIVAS AS TotalIVAS, "
            "FacturaCliente.IdTurno AS IdTurno, "
            "FacturaCliente.HoraEntrega AS HoraEntrega, "
            "FacturaCliente.CodigoElectronico AS CodigoElectronico, "
            "FacturaCliente.Propina AS Propina, "
            "FacturaCliente.TotalICE AS TotalICE, "
            "FacturaCliente.Placa AS Placa, "
            "FacturaCliente.IdentificacionCliente AS IdentificacionCliente, "
            "FacturaCliente.NombreCliente AS NombreCliente, "
            "FacturaCliente.TipoEmision AS TipoEmision, "
            "FacturaCliente.CodigoCara AS CodigoCara, "
            "FacturaCliente.PuntosAcumulados AS PuntosAcumulados, "
            "FacturaCliente.TotalaPagar AS TotalaPagar, "
            "FacturaCliente.SecuenciaVenta AS SecuenciaVenta, "
            "FacturaCliente.Facturada AS Facturada, "
            "FacturaCliente.Fidelizada AS Fidelizada, "
            "FacturaCliente.FormasPago AS FormasPago, "
            "FacturaCliente.TipoVenta AS TipoVenta, "
            "FacturaCliente.CodigoIsla AS CodigoIsla, "
            "FacturaCliente.DatosImpresionFactura AS DatosImpresionFactura, "
            "FacturaCliente.FechaProximaRevicion, "
            "FacturaCliente.Kilometraje, "
            "FacturaCliente.IdentificacionConductor, "
            "FacturaCliente.NombreConductor, "
            "FacturaCliente.VentaConvertida, "
            "FacturaCliente.IdVentaEstacion, "
            "Venta.ValorAutorizado AS ValorAutorizado, "
            "(Venta.ValorAutorizado - Venta.ValorVenta) AS Cambio, "
            "ISNULL(Venta.VolumenVenta,0) AS Volumen, "
            "ISNULL(FacturaCliente.Anulada,0) AS Anulada, "
            "ISNULL(FacturaCliente.panterapago,0) AS panterapago, "
            "FacturaClienteFidelizada.Mensaje AS MensajeFidelizacion, "
            "FacturaClienteFidelizada.Estado AS FidelizacionActiva, "
            "FormaPagoVenta.XMLConsolidador, "
            "ClienteOffLine.Correo AS CorreoCliente "
            "FROM dbo.FacturaCliente WITH(NOLOCK) "
            "LEFT JOIN dbo.Venta WITH(NOLOCK) "
            "ON FacturaCliente.IdVentaEstacion = Venta.CodigoVenta "
            "AND FacturaCliente.TipoVenta IN (1, 2) "
            "LEFT JOIN dbo.FacturaClienteFidelizada WITH(NOLOCK) "
            "ON FacturaCliente.IdFacturaCliente = FacturaClienteFidelizada.IdFacturaCliente "
            "LEFT JOIN dbo.FormaPagoVenta WITH(NOLOCK) "
            "ON FormaPagoVenta.IdDocumento = FacturaCliente.IdDocumento "
            "AND FormaPagoVenta.IdTurno = FacturaCliente.IdTurno "
            "LEFT JOIN dbo.ClienteOffLine WITH(NOLOCK) "
            "ON ClienteOffLine.Identificacion = FacturaCliente.IdentificacionCliente "
            f"WHERE {where} ORDER BY FacturaCliente.Fecha DESC",
            SqlRow,
            parameters=tuple(params),
        )

    return {
        'ListarPlacasClienteOffline': (NoParameters, plates),
        'ConsultarIdentificadorAutomotor': (AutomotorKey, automotor),
        'ConsultarTurnoResumido': (ShiftIdParam, shift_summary),
        'ListarGastosTurnoDetalle': (NoParameters, expenses),
        'ListarAuditoriaContingencia': (NoParameters, audits),
        'ListarPreciosProgramadosPorIsla': (IslandCodeParam, prices_by_island),
        'ListarFacturasClienteConvertidas': (ConvertedInvoiceFilter, converted),
        'ConsultarFacturaClienteConvertida': (ConvertedInvoiceFilter, converted),
        'ListarFacturasClienteTurno': (ShiftInvoiceFilter, shift_invoices),
    }


def bridge_write_operations(db: SqlDatabase) -> dict[str, Operation]:
    def affected(sql, params):
        count = db.write([(sql, params)], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def insert_bag(**values):
        return affected(
            "INSERT INTO dbo.BolsasTurno "
            "(IdTurno, CodigoBolsa, ValorBillete, ValorMoneda, FechaZeta, "
            "HoraTurno, Sincronizo, Nota) VALUES (?,?,?,?,?,?,?,?)",
            (values['idTurno'], values['codigoBolsa'], values['valorBillete'],
             values['valorMoneda'], values['fechaZeta'], values['horaTurno'],
             values['sincronizo'], values['nota']),
        )

    def insert_audit(**values):
        return affected(
            "INSERT INTO dbo.AuditoriaContingencia "
            "(Fecha, Proceso, Usuario, Descripcion) VALUES (?,?,?,?)",
            (values['fecha'], values['proceso'], values['usuario'],
             values['descripcion']),
        )

    def update_dispatch(**values):
        return affected(
            "UPDATE dbo.predespacho_cliente "
            "SET estado = ?, fechamodificacion = SYSDATETIME() "
            "WHERE idpredespachocliente = ?",
            (values['estado'], values['idPredespachoCliente']),
        )

    def insert_payment_method(**values):
        return affected(
            "EXEC dbo.InsertarFormaPagoSiNoExiste "
            "@IdFormaPago = ?, @Nombre = ?, @Codigo = ?",
            (values['idFormaPago'], values['nombre'], values['codigo']),
        )

    def update_accumulator(**values):
        return affected(
            "EXEC dbo.actualizarAcumuladoraFormaPago "
            "@IdTurno = ?, @CodFp = ?, @Valor = ?",
            (values['idTurno'], values['codFp'], values['valor']),
        )

    def insert_payment_sale(**values):
        return affected(
            "INSERT INTO dbo.FormaPagoDetalleVenta "
            "(IdVenta, IdTurno, IdVentaAdicional, Valor) VALUES (?,?,?,?)",
            (values['idVenta'], values['idTurno'], values['idVentaAdicional'],
             values['valor']),
        )

    def save_medianet(**values):
        return affected(
            "EXEC dbo.sp_GuardarConfiguracionMediaNet "
            "@id = ?, @ip = ?, @mascara = ?, @gateway = ?, "
            "@hostPrinciR1Ip = ?, @hostPrinciR1Puerto = ?, "
            "@hostAlterR1Ip = ?, @hostAlterR1Puerto = ?, "
            "@hostPrinciR2Ip = ?, @hostPrinciR2Puerto = ?, "
            "@hostAlterR2Ip = ?, @hostAlterR2Puerto = ?, "
            "@puertoEscucha = ?",
            (values.get('id'), values['ip'], values['mascara'], values['gateway'],
             values['hostPrinciR1Ip'], values['hostPrinciR1Puerto'],
             values['hostAlterR1Ip'], values['hostAlterR1Puerto'],
             values['hostPrinciR2Ip'], values['hostPrinciR2Puerto'],
             values['hostAlterR2Ip'], values['hostAlterR2Puerto'],
             values['puertoEscucha']),
        )

    def insert_payment_detail(**values):
        keys = (
            'idVenta', 'idTurno', 'identificacionRed', 'codigoRespuestaActor',
            'mensajeRespuesta', 'secuencialTransaccion', 'numeroLote',
            'horaTransaccion', 'fechaTransaccion', 'numeroAutorizacion', 'tid',
            'mid', 'valorInteres', 'mensajeImpresion', 'codigoBanco',
            'nombreBanco', 'nombreGrupoTarjeta', 'modoLectura',
            'nombreTarjetaHabiente', 'montoFijo', 'identificadorAplicacion',
            'aid', 'tipoCrigtograma', 'pin', 'arqc', 'numeroTarjetaTruncado',
            'fechaVencimientoTarjeta', 'numeroTarjetaEncriptada', 'impuesto',
            'baseConImpuesto', 'baseSinImpuesto', 'montoImpuesto', 'montoTotal',
            'idFormaPago', 'host', 'hostName', 'tipoTarjeta', 'tipoVenta',
            'numeroTarjeta', 'loteAbierto', 'nombreTH', 'aprobacion',
            'idTerminal', 'numeroReferencia', 'codigoReferencia', 'idComercio',
            'diferidoyQuickPayment', 'reservado', 'archivoFirma', 'tvr', 'tsi',
            'idCashBack', 'anulada', 'multiplesVentas',
        )
        params = tuple(values.get(key) for key in keys)
        return affected(
            "EXEC dbo.sp_InsertarFormaPagoDetalle "
            "@IdVenta=?, @IdTurno=?, @IdentificacionRed=?, "
            "@CodigoRespuestaActor=?, @MensajeRespuesta=?, "
            "@SecuencialTransaccion=?, @NumeroLote=?, @HoraTransaccion=?, "
            "@FechaTransaccion=?, @NumeroAutorizacion=?, @TID=?, @MID=?, "
            "@ValorInteres=?, @MensajeImpresion=?, @CodigoBanco=?, "
            "@NombreBanco=?, @NombreGrupoTarjeta=?, @ModoLectura=?, "
            "@NombreTarjetaHabiente=?, @MontoFijo=?, "
            "@IdentificadorAplicacion=?, @AID=?, @TipoCrigtograma=?, "
            "@PIN=?, @ARQC=?, @NumeroTarjetaTruncado=?, "
            "@FechaVencimientoTarjeta=?, @NumeroTarjetaEncriptada=?, "
            "@Impuesto=?, @BaseConImpuesto=?, @BaseSinImpuesto=?, "
            "@MontoImpuesto=?, @MontoTotal=?, @IdFormaPago=?, @Host=?, "
            "@HostName=?, @TipoTarjeta=?, @TipoVenta=?, @NumeroTarjeta=?, "
            "@LoteAbierto=?, @NombreTH=?, @Aprobacion=?, @IdTerminal=?, "
            "@NumeroReferencia=?, @CodigoReferencia=?, @IdComercio=?, "
            "@DiferidoyQuickPayment=?, @Reservado=?, @ArchivoFirma=?, "
            "@TVR=?, @TSI=?, @IdCashBack=?, @Anulada=?, @MultiplesVentas=?",
            params,
        )

    def insert_payment_other(**values):
        # Misma firma flexible del SP de detalle otros.
        return affected(
            "EXEC dbo.sp_InsertarFormaPagoDetalleOtros "
            "@IdVenta=?, @IdTurno=?, @IdFormaPago=?, @Valor=?, "
            "@NumeroReferencia=?, @NumeroAutorizacion=?, @Observacion=?",
            (
                values.get('idVenta'), values.get('idTurno'),
                values.get('idFormaPago'), values.get('valor'),
                values.get('numeroReferencia'), values.get('numeroAutorizacion'),
                values.get('observacion'),
            ),
        )

    def insert_loyalty(**values):
        return affected(
            "INSERT INTO dbo.MovimientoFidelizacion "
            "(IdTurno, IdDocumento, Acumulado, Redimido, BalanceActual, "
            "PuntosActivos, IdentificacionFidelizado, NombreFidelizado, "
            "Mensaje, Fecha, ValorRedimido, IdTransaccion, Estado, "
            "ValorAcumulado, IdTipoIdentificacion, TipoPrograma, "
            "IdTipoIdentificacionPromocion, NombreClientePromocion, "
            "IdentificacionPromocion, IdTipoVehiculo) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                values.get('idTurno'), values.get('idDocumento'),
                values.get('acumulado'), values.get('redimido'),
                values.get('balanceActual'), values.get('puntosActivos'),
                values.get('identificacionFidelizado'),
                values.get('nombreFidelizado'), values.get('mensaje'),
                values.get('fecha'), values.get('valorRedimido'),
                values.get('idTransaccion'), values.get('estado'),
                values.get('valorAcumulado'),
                values.get('idtipoidentificacion'),
                values.get('tipoPrograma'),
                values.get('idTipoIdentificacionPromocion'),
                values.get('nombreClientePromocion'),
                values.get('identificacionPromocion'),
                values.get('idTipoVehiculo'),
            ),
        )

    def accumulator_batch(**values):
        items = values.get('items') or []
        statements = []
        for item in items:
            statements.append((
                "EXEC dbo.actualizarAcumuladoraFormaPago "
                "@IdTurno = ?, @CodFp = ?, @Valor = ?",
                (values['idTurno'], item.get('codFp') or item.get('codigo'),
                 item.get('valor')),
            ))
        if not statements:
            return [SqlAffectedRows(affectedRows=0)]
        count = db.write(statements, count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def delete_prices(*, codigoIsla: int):
        return affected(
            "DELETE FROM dbo.ArticuloPrecioProgramado WHERE CodigoIsla = ?",
            (str(codigoIsla),),
        )

    def update_general(*, llave: str, valor):
        from app.errors import ApiError
        if llave not in _GENERAL_CONFIG_KEYS:
            raise ApiError(400, 'INVALID_PARAMETERS', 'Llave de ConfiguracionGeneral no permitida')
        return affected(
            f"UPDATE dbo.ConfiguracionGeneral SET [{llave}] = ?",
            (valor,),
        )

    def update_invoice_payment(**values):
        return affected(
            "EXEC dbo.actualizarFacturaClienteYFormasPago "
            "@IDFacturaCliente=?, @IDFormaPago=?, @FormasPago=?, "
            "@IdTurno=?, @CodFp=?, @Valor=?, @IdDocumento=?, "
            "@IdCompania=?, @IdCentroVenta=?, @CodigoCara=?, "
            "@IdUltimaVenta=?, @XMLConsolidador=?, @XMLFactura=?, "
            "@Sincronizada=?, @CodigoIsla=?, @IdVenta=?, @EsUpdate=?",
            (
                values['idFacturaCliente'], values['idFormaPago'],
                values['formasPago'], values['idTurno'], values['codFp'],
                values['valor'], values['idDocumento'], values['idCompania'],
                values['idCentroVenta'], values['codigoCara'],
                values['idDocumento'], values['xmlConsolidador'],
                values['xmlFactura'], int(values['sincronizada']),
                values['codigoIsla'], values['idDocumento'],
                int(values['esUpdate']),
            ),
        )

    return {
        'InsertarBolsaTurno': (BagInsert, insert_bag),
        'InsertarAuditoriaContingencia': (AuditInsert, insert_audit),
        'ActualizarEstadoPredespachoCliente': (DispatchState, update_dispatch),
        'InsertarFormaPagoSiNoExiste': (PaymentMethodInsert, insert_payment_method),
        'ActualizarAcumuladoraFormaPago': (AccumulatorUpdate, update_accumulator),
        'ActualizarAcumuladoraFormaPagoBatch': (FlexibleParameters, accumulator_batch),
        'InsertarFormaPagoDetalleVenta': (PaymentDetailSale, insert_payment_sale),
        'GuardarConfiguracionMediaNet': (MedianetConfig, save_medianet),
        'InsertarFormaPagoDetalle': (FlexibleParameters, insert_payment_detail),
        'InsertarFormaPagoDetalleOtros': (FlexibleParameters, insert_payment_other),
        'InsertarMovimientoFidelizacion': (FlexibleParameters, insert_loyalty),
        'EliminarPreciosProgramadosPorIsla': (IslandCodeParam, delete_prices),
        'ActualizarConfiguracionGeneralLlave': (GeneralConfigKey, update_general),
        'ActualizarFacturaClienteYFormasPago': (InvoicePaymentSimple, update_invoice_payment),
    }
