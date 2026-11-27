from functools import cache
from importlib.resources import files
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.core.database import SqlDatabase
from app.core.registry import Operation, request_actor
from app.errors import ApiError
from app.schemas import NoParameters, SqlScalar, StrictModel
from app.modules.article.operations import SqlAffectedRows


class InvoiceIds(StrictModel):
    ids: list[Annotated[int, Field(ge=-2147483648, le=2147483647)]] = Field(max_length=5000)


class SqlRow(BaseModel):
    model_config = ConfigDict(extra='allow')


class FlexibleParameters(BaseModel):
    model_config = ConfigDict(extra='allow')


class CashbackWrite(StrictModel):
    idTurno: int
    codigoFp: int
    valor: float
    fee: float
    total: float
    identificacion: str
    nombre: str
    telefono: str
    incluyeVenta: bool
    idDocumento: int
    sincronizado: bool


class InvoiceNumberRequest(StrictModel):
    nIdCompania: int
    nIdcv: int
    nIdPV: int
    sCodComprobante: str
    gnCodigoArea: str
    nCanastilla: int
    pActualizarResolution: bool


class DeliveryCreate(StrictModel):
    numeroActaEntrega: int
    identificacion: str
    nombreCliente: str
    totalRedimido: float
    fecha: str
    idTurno: int
    detalles: str


class VoidedPaymentUpdate(StrictModel):
    idVenta: int


class PresetFilter(StrictModel):
    idTurno: int | None = None


class ShiftId(StrictModel):
    idTurno: int


class ShiftInvoicePayments(ShiftId):
    top: int = Field(ge=1, le=2147483647)


class FaceShift(ShiftId):
    cara: int
    codigoIsla: int


class FaceOnly(StrictModel):
    cara: int


class PaymentDetailsFilter(StrictModel):
    idTurno: int | None = None
    idVenta: int | None = None
    idsVentas: list[int] | None = Field(default=None, max_length=5000)


class CashbackFilter(StrictModel):
    idTurno: int | None = None
    idCashBack: int | None = None
    numero: int | None = None
    top: int = Field(default=1, ge=1, le=1000)


class CreditSalesState(StrictModel):
    idVentaEstacion: int
    estado: int


class CreditSalesDeliveryState(CreditSalesState):
    tipoEnvio: str


class AuthorizationPendingFilter(StrictModel):
    isla: int


class AuthorizationPendingUpdate(StrictModel):
    idAutorizacionPendiente: int


class ExternalAuthorizationFilter(StrictModel):
    idCompania: int
    caras: list[int] = Field(max_length=100)


class ExternalAuthorizationWrite(StrictModel):
    idCompania: int
    informacion: str
    process: int
    mensaje: str
    fechaEjecucion: str | None = None
    fechaInsercion: str | None = None
    autorizado: int
    cara: int


class ExternalAuthorizationUpdate(StrictModel):
    idAutorizacion: int
    process: int
    mensaje: str
    autorizado: int


class InventoryUpdate(StrictModel):
    idArticulo: int
    idPV: int
    cantidad: float


class InvoiceLine(BaseModel):
    IdTipoDocumento: SqlScalar
    IdDocumento: SqlScalar
    IdFacturaClienteDetalle: SqlScalar
    IdArticulo: SqlScalar
    IdTarifaIVA: SqlScalar
    Cantidad: SqlScalar
    ValorUnitario: SqlScalar
    PorcentajeIVA: SqlScalar
    PorcentajeDescuento: SqlScalar
    Subtotal: SqlScalar
    ValorIVA: SqlScalar
    Total: SqlScalar
    ValorDescuento: SqlScalar
    CodigoICE: SqlScalar
    PorcentajeICE: SqlScalar
    ValorICE: SqlScalar
    PrecioSinSubsidioECU: SqlScalar
    Presentacion: SqlScalar
    FactorSubsidoECU: SqlScalar
    CodigoArticulo: SqlScalar
    Articulo: SqlScalar
    IncluyeIVA: SqlScalar
    ImprimirNombreContro: SqlScalar
    IdFacturaCliente: SqlScalar
    ImpuestoValorFijo: SqlScalar
    CodigoAlterno: SqlScalar
    NombreCorto: SqlScalar
    IdArticuloCombustible: SqlScalar


@cache
def invoice_lines_sql() -> str:
    return files(__package__).joinpath('queries', 'lines.sql').read_text(encoding='utf8')


class InvoiceLoyaltyFilter(InvoiceIds):
    soloConAcumuladoMayorACero: bool = True


class InvoiceLoyaltyMovementFilter(StrictModel):
    tipoPrograma: int
    idTurno: int


class InvoiceLoyaltyRow(BaseModel):
    IdFacturaCliente: SqlScalar
    Acumulado: SqlScalar
    Redimido: SqlScalar
    BalanceActual: SqlScalar
    PuntosActivos: SqlScalar
    IdentificacionFidelizado: SqlScalar
    NombreFidelizado: SqlScalar
    Mensaje: SqlScalar
    Fecha: SqlScalar
    ValorRedimido: SqlScalar
    IdTransaccion: SqlScalar
    Estado: SqlScalar
    ValorAcumulado: SqlScalar
    idtipoidentificacion: SqlScalar
    TipoPrograma: SqlScalar
    IdTipoIdentificacionPromocion: SqlScalar
    NombreClientePromocion: SqlScalar
    IdentificacionPromocion: SqlScalar
    IdTipoVehiculo: SqlScalar


class InvoiceLoyaltyMovementRow(InvoiceLoyaltyRow):
    PrefijoFactura: SqlScalar
    NumeroFactura: SqlScalar


class DeliveryId(StrictModel):
    idActaEntrega: int


class DeliveryShift(StrictModel):
    idTurno: int


class SaleCodeRow(BaseModel):
    IdVenta: SqlScalar
    CodigoCara: SqlScalar
    IdentificacionCliente: SqlScalar
    Placa: SqlScalar
    CodigoArticulo: SqlScalar
    ValorAutorizado: SqlScalar
    NombreCliente: SqlScalar
    Credito: SqlScalar
    Kilometraje: SqlScalar
    Estado: SqlScalar
    CodigoVenta: SqlScalar
    ValorUnitario: SqlScalar
    ValorVenta: SqlScalar
    VolumenVenta: SqlScalar
    CodigoPOS: SqlScalar
    CodigoManguera: SqlScalar
    CodigoIsla: SqlScalar
    FactorPrecio: SqlScalar
    CodigoCliente: SqlScalar
    Calibracion: SqlScalar
    Fecha: SqlScalar
    FactorVenta: SqlScalar
    FactorVolumen: SqlScalar
    Prepago: SqlScalar
    IdTurno: SqlScalar
    IdSecuencial: SqlScalar
    NumeroCapturador: SqlScalar
    IdTranControladora: SqlScalar
    TipoEmision: SqlScalar
    TipoPreset: SqlScalar
    FechaAutorizacion: SqlScalar
    precio_especial: SqlScalar


class SaleCheckRow(BaseModel):
    IdVentaEstacion: SqlScalar
    Cara: SqlScalar
    Estado: SqlScalar
    IdTurno: SqlScalar
    IdDocumento: SqlScalar


class DeliveryRow(BaseModel):
    IdActaEntrega: SqlScalar
    NumeroActaEntrega: SqlScalar
    Identificacion: SqlScalar
    NombreCliente: SqlScalar
    TotalRedimido: SqlScalar
    Fecha: SqlScalar
    IdTurno: SqlScalar


class DeliveryLineRow(BaseModel):
    IdActaEntregaDetalle: SqlScalar
    IdActaEntrega: SqlScalar
    Premio: SqlScalar
    Cantidad: SqlScalar
    TotalPuntos: SqlScalar
    TotalValorEmpresa: SqlScalar


class PresetWrite(StrictModel):
    cantidad: float
    hora: str
    cara: int
    tipo: int
    idTurno: int
    producto: str


class PrinterWidthWrite(StrictModel):
    codigoIsla: int
    impresoraCaracteresNumero: int


class InvoiceId(StrictModel):
    idFacturaCliente: int = Field(ge=1, le=2147483647)


class InvoiceCufe(InvoiceId):
    cufe: str


class CreditNoteWrite(InvoiceId):
    prefijo: str
    numeroNotaCredito: str
    numeroAutorizacion: str
    fecha: str


class CreditNoteRow(BaseModel):
    IdNotaCredito: SqlScalar
    IdFacturaCliente: SqlScalar
    Prefijo: SqlScalar
    NumeroNotaCredito: SqlScalar
    NumeroAutorizacion: SqlScalar
    Fecha: SqlScalar


class InvoiceLoyalty(InvoiceId):
    fidelizada: bool


class InvoiceVoided(InvoiceId):
    anulada: bool


class InvoiceLoyaltyState(InvoiceId):
    state: int = Field(ge=-2147483648, le=2147483647)


class CompleteInvoiceFilter(StrictModel):
    nMinutosMaximo: int | None = None
    idTipoDocumento: int | None = None
    topN: int | None = None
    idFacturaCliente: int | None = None
    idsFacturaCliente: list[int] | None = None
    idDocumento: str | None = None
    idTurno: int | None = None
    identificacionCliente: str | None = None
    tipoVentaExcluido: str | None = None
    codigoIsla: str | None = None
    numeroFactura: str | None = None
    soloConvertidos: bool = False
    fromFormaPago: bool = False
    notaCredito: bool = False
    isIdDocumento: bool = False


class CompleteInvoiceSets(BaseModel):
    resultSets: list[list[dict[str, SqlScalar]]]


class InvoiceDetailSetsFilter(StrictModel):
    ids: list[int] = Field(max_length=5000)
    idVentas: list[int] = Field(max_length=5000)


class SaleSequence(StrictModel):
    nIsla: int = Field(gt=0, le=2147483647)
    nnumCapturador: int = Field(ge=0, le=2147483647)


class SaleSequenceRow(BaseModel):
    consecutivo: int
    mensaje: str = ""


class ResolutionWrite(StrictModel):
    idCompania: int
    idResolucion: int
    idCentroVenta: int
    idPuntoVenta: int
    idListaTipoResolucion: int
    numeroInicial: int
    numeroFinal: int
    fechaAsignacionResolucion: str
    numeroResolucion: str
    prefijoFacturacion: str
    estadoResolucion: str
    fechaExpiracionResolucion: str
    ultimoNumeroAsignado: int
    leyenda1: str
    leyenda2: str
    leyenda3: str
    diasParaVencimiento: int
    alertaCantidad: int
    divisionNegocio: str
    codigoComprobante: str
    claveTecnica: str


class SaleProcessXml(StrictModel):
    idVenta: int = Field(ge=-2147483648, le=2147483647)
    xmlFacturacion: str
    xmlFidelizacion: str
    xmlConsolidacion: str
    idFactura: int | None = Field(default=None, ge=-2147483648, le=2147483647)


class CreditSaleProcessXml(SaleProcessXml):
    idVenta: str = Field(pattern=r"^[0-9]{1,38}$")


class SaleCheckState(StrictModel):
    idVentaEstacion: int
    estado: int


class RaffleState(BaseModel):
    AplicaSorteo: int | None


@cache
def invoice_operation_sql(filename: str) -> str:
    return files(__package__).joinpath('queries', filename).read_text(encoding='utf8')


def invoice_station():
    station, _ = request_actor.get()
    try:
        company, center, island = (int(part) for part in station.split('/'))
    except ValueError:
        raise ApiError(403, 'INVALID_STATION', 'Perfil de estación inválido') from None
    return island, company, center, island


def invoice_operations(db: SqlDatabase) -> dict[str, Operation]:
    def lines(*, ids: list[int]):
        station, _ = request_actor.get()
        try:
            company, center, island = (int(part) for part in station.split('/'))
        except ValueError:
            raise ApiError(403, 'INVALID_STATION', 'Perfil de estación inválido') from None
        if not ids:
            return []
        xml = '<Ids>' + ''.join(f'<Id>{item}</Id>' for item in ids) + '</Ids>'
        return db.read(invoice_lines_sql(), InvoiceLine, parameters=(xml, company, center, island))

    def raffle_state(*, idFacturaCliente: int):
        return db.read(
            invoice_operation_sql('raffle_state.sql'), RaffleState,
            parameters=(idFacturaCliente, *invoice_station()),
        )

    def write(filename, *keys):
        def execute(*, idFacturaCliente: int, **values):
            count = db.write([
                (invoice_operation_sql(filename),
                 (*(values[key] for key in keys), idFacturaCliente, *invoice_station())),
            ], count_rows=True)
            return [SqlAffectedRows(affectedRows=count)]
        return execute

    def sale_xml(filename, **values):
        island, company, center, _ = invoice_station()
        params = (values['xmlFacturacion'], values['xmlFidelizacion'],
                  values['xmlConsolidacion'], values['idFactura'], values['idVenta'],
                  island, center, company)
        count = db.write([(invoice_operation_sql(filename), params)], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def save_resolution(**values):
        keys = ('idCompania', 'idResolucion', 'idCentroVenta', 'idPuntoVenta', 'idListaTipoResolucion', 'numeroInicial', 'numeroFinal', 'fechaAsignacionResolucion', 'numeroResolucion', 'prefijoFacturacion', 'estadoResolucion', 'fechaExpiracionResolucion', 'ultimoNumeroAsignado', 'leyenda1', 'leyenda2', 'leyenda3', 'diasParaVencimiento', 'alertaCantidad', 'divisionNegocio', 'codigoComprobante', 'claveTecnica')
        count = db.write([
            (invoice_operation_sql('upsert_resolution.sql'), tuple(values[key] for key in keys)),
        ], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def complete_invoice(**values):
        island, company, center, _ = invoice_station()
        ids = values['idsFacturaCliente']
        csv_ids = ','.join(map(str, ids)) if ids else None
        params = (company, center, island, values['nMinutosMaximo'], values['idTipoDocumento'],
                  values['topN'], values['idFacturaCliente'], csv_ids, values['idDocumento'],
                  values['idTurno'], values['identificacionCliente'], values['tipoVentaExcluido'],
                  str(island), values['numeroFactura'], values['soloConvertidos'],
                  values['fromFormaPago'], values['notaCredito'], values['isIdDocumento'])
        rows = db.read_result_sets(invoice_operation_sql('complete_invoice.sql'), params)
        return [CompleteInvoiceSets(resultSets=rows)]

    def invoice_headers(**values):
        return [SqlRow.model_validate(row) for row in complete_invoice(**values)[0].resultSets[0]]

    def invoice_detail_sets(*, ids, idVentas):
        loyalty = read_loyalty(ids=ids, soloConAcumuladoMayorACero=True)
        promotions = read_promotions(ids=ids)
        payments = payment_details(idTurno=None, idVenta=None, idsVentas=idVentas)
        details = lines(ids=ids)
        return [CompleteInvoiceSets(resultSets=[
            [row.model_dump() for row in loyalty],
            [row.model_dump() for row in promotions],
            [row.model_dump() for row in payments],
            [row.model_dump() for row in details],
        ])]

    def credit_note_exists(*, idFacturaCliente):
        return db.read(invoice_operation_sql('credit_note_by_invoice.sql'), CreditNoteRow,
                       parameters=(idFacturaCliente, *invoice_station()))

    def insert_credit_note(*, idFacturaCliente, prefijo, numeroNotaCredito, numeroAutorizacion, fecha):
        count = db.write([(invoice_operation_sql('insert_credit_note.sql'),
                          (prefijo, numeroNotaCredito, numeroAutorizacion, fecha,
                           idFacturaCliente, *invoice_station()))], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def sale_sequence(*, nIsla, nnumCapturador):
        island, company, center, _ = invoice_station()
        return db.write([(invoice_operation_sql('sale_sequence.sql'),
                          (company, center, island, nIsla, nnumCapturador))],
                        result_model=SaleSequenceRow)

    def set_sale_check(*, idVentaEstacion, estado):
        count = db.write([(invoice_operation_sql('update_sale_check.sql'),
                          (estado, idVentaEstacion, *invoice_station()))], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def reset_pending_sales():
        count = db.write([(invoice_operation_sql('reset_pending_sales.sql'),
                          invoice_station())], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def read_loyalty(*, ids, soloConAcumuladoMayorACero):
        if not ids:
            return []
        xml = '<Ids>' + ''.join(f'<Id>{value}</Id>' for value in ids) + '</Ids>'
        return db.read(invoice_operation_sql('loyalty_by_invoice.sql'), InvoiceLoyaltyRow,
                       parameters=(xml, soloConAcumuladoMayorACero, *invoice_station()))

    def read_promotions(*, ids):
        if not ids:
            return []
        xml = '<Ids>' + ''.join(f'<Id>{value}</Id>' for value in ids) + '</Ids>'
        return db.read(invoice_operation_sql('promotions_by_invoice.sql'), InvoiceLoyaltyRow,
                       parameters=(xml, *invoice_station()))

    def read_loyalty_movements(*, tipoPrograma, idTurno):
        return db.read(invoice_operation_sql('loyalty_movements.sql'), InvoiceLoyaltyMovementRow,
                       parameters=(tipoPrograma, idTurno, *invoice_station()))

    def read_sql_row(filename, parameters=()):
        return db.read(invoice_operation_sql(filename), SqlRow, parameters=parameters)

    def credit_notes():
        return read_sql_row('credit_notes.sql', invoice_station())

    def face_state(*, cara, idTurno, codigoIsla):
        island, company, center, _ = invoice_station()
        return read_sql_row('face_state.sql', (cara, idTurno, codigoIsla, company, center, island))

    def payment_details(*, idTurno, idVenta, idsVentas):
        xml = None if idsVentas is None else '<Ids>' + ''.join(f'<Id>{value}</Id>' for value in idsVentas) + '</Ids>'
        return read_sql_row('payment_details.sql', (xml, idVenta, idVenta, idTurno, idTurno, *invoice_station()))

    def shift_invoice_payments(*, idTurno, top):
        return read_sql_row('shift_invoice_payments.sql', (top, idTurno, *invoice_station()))

    def cashback_next(*, idTurno):
        return read_sql_row('cashback_next.sql', (idTurno, *invoice_station()))

    def cashback_by_shift(*, idTurno):
        return read_sql_row('cashback_by_shift.sql', (idTurno, *invoice_station()))

    def cashback_rows(*, idTurno, idCashBack, numero, top):
        island, company, center, _ = invoice_station()
        return read_sql_row(
            'cashback_rows.sql',
            (company, center, island, idTurno, idTurno, island,
             idTurno, idCashBack, numero, top),
        )

    def canje(*, cara):
        island, company, center, _ = invoice_station()
        return read_sql_row('exchange_value.sql', (company, center, island, island, cara))

    def update_credit_sale(filename, **values):
        count = db.write([(invoice_operation_sql(filename),
                          (*(values[key] for key in ('estado', 'tipoEnvio') if key in values),
                           values['idVentaEstacion'], *invoice_station()))], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def authorization_pending(*, isla):
        island, company, center, _ = invoice_station()
        return read_sql_row('authorization_pending.sql', (isla, company, center, island))

    def authorization_pending_update(*, idAutorizacionPendiente):
        count = db.write([(invoice_operation_sql('authorization_pending_update.sql'),
                          (idAutorizacionPendiente, *invoice_station()))], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def external_authorizations(*, idCompania, caras):
        _, company, center, island = invoice_station()
        if idCompania != company or not caras:
            return []
        xml = '<Ids>' + ''.join(f'<Id>{value}</Id>' for value in caras) + '</Ids>'
        return read_sql_row('external_authorizations.sql', (xml, company, center, island))

    def external_authorization_insert(**values):
        _, company, center, island = invoice_station()
        keys = ('idCompania', 'informacion', 'process', 'mensaje', 'fechaEjecucion',
                'fechaInsercion', 'autorizado', 'cara')
        count = db.write([(invoice_operation_sql('external_authorization_insert.sql'),
                          (company, center, *(values[key] for key in keys)))], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def external_authorization_update(**values):
        keys = ('process', 'mensaje', 'autorizado', 'idAutorizacion')
        count = db.write([(invoice_operation_sql('external_authorization_update.sql'),
                          (*(values[key] for key in keys), *invoice_station()))], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def update_inventory(**values):
        count = db.write([(invoice_operation_sql('update_inventory.sql'),
                          (values['cantidad'], values['idArticulo'], values['idPV'],
                           *invoice_station()))], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def cashback_write(**values):
        keys = ('idTurno', 'codigoFp', 'valor', 'fee', 'total', 'identificacion',
                'nombre', 'telefono', 'incluyeVenta', 'idDocumento', 'sincronizado')
        return db.write([(invoice_operation_sql('cashback_insert.sql'),
                          tuple(values[key] for key in keys))], result_model=SqlRow)

    def invoice_number(**values):
        island, company, center, _ = invoice_station()
        keys = ('nIdCompania', 'nIdcv', 'nIdPV', 'sCodComprobante',
                'gnCodigoArea', 'nCanastilla', 'pActualizarResolution')
        params = (island, *(values[key] for key in keys))
        return db.write([(invoice_operation_sql('invoice_number.sql'), params)],
                        result_model=SqlRow)

    def delivery_create(**values):
        keys = ('numeroActaEntrega', 'identificacion', 'nombreCliente',
                'totalRedimido', 'fecha', 'idTurno', 'detalles')
        return db.write([(invoice_operation_sql('delivery_insert.sql'),
                          tuple(values[key] for key in keys))], result_model=SqlRow)

    def voided_payment_update(*, idVenta):
        count = db.write([(invoice_operation_sql('voided_payment_update.sql'),
                          (idVenta, *invoice_station()))], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def station_flexible_write(filename, keys, **values):
        return db.write([(invoice_operation_sql(filename),
                          tuple(values.get(key) for key in keys))], result_model=SqlRow)

    def evaluate_discount(**values):
        keys = ('idArticulo', 'cara', 'idManguera', 'valorTotal', 'valorUnitario',
                'cantidad', 'idFormaPago', 'romVenta', 'tipoVenta',
                'codArticuloString', 'placa', 'identificacion')
        return station_flexible_write('evaluate_discount.sql', keys, **values)

    def update_invoice_customer(**values):
        keys = ('idDocumento', 'placa', 'identificacionCliente', 'kilometraje',
                'identificacionConductor', 'nombreCliente', 'nombreConductor', 'correo',
                'idTurno', 'idVenta', 'codigoIsla', 'codigoCultura', 'idCompania',
                'idCentroVenta', 'idPuntoVenta', 'idResolucion', 'numeroFactura',
                'codigoComprobante', 'ventaCredito', 'idTransaccion',
                'realizoConsolidacion', 'errorConsolidacion')
        return station_flexible_write('update_invoice_customer.sql', keys, **values)

    def insert_sale_check(**values):
        keys = ('idTurno', 'idVentaEstacion', 'codigoIsla', 'peticion', 'cara', 'estado',
                'formaPago', 'fechaProximaRevision', 'rom', 'clavePrepago',
                'identificacionConductor', 'nombreConductor', 'identPasaporte',
                'totalFleet', 'generaNotaEntrega', 'ventaCHIPIslero', 'idAuthOffline',
                'facturarConductor', 'barCodeAutomotor', 'tipoAuth', 'idTransaccionCupo',
                'datosTransaccion', 'datosPreciosEDS', 'idtipovehiculo', 'clienteQR',
                'manifiesto', 'generaTicketEfectivoEDS', 'isCreditoContingencia',
                'uid', 'acumulaPuntos')
        return station_flexible_write('sale_check_insert.sql', keys, **values)

    def insert_credit_sale(**values):
        keys = ('idTransaccion', 'idTurno', 'idVentaEstacion', 'placa',
                'identificacionCliente', 'estado', 'cara', 'clavePrepago', 'tipoEnvio',
                'realizoConsolidacion', 'descripcion', 'tipoAutorizacion', 'cupoExterno',
                'envioCupoExterno', 'resultadoCupoExterno', 'manifiesto', 'reintentos',
                'uid', 'valorautorizado')
        return station_flexible_write('credit_sale_insert.sql', keys, **values)

    def insert_invoice_fast(**values):
        keys = ('isla','idCompania','idCentroVenta','idPuntoVenta','codComprobante','nCalibracion','bGeneraNotaEntrega','nCodFp','bCreditoFactura','nCanastilla','nIdTurno','nIdTipoDocumento','nCodigoIsla','sFechaFormateada','nHoraEntrega','sIdentificacionCliente','sNombreCliente','sFormasPago','sPlaca','sKilometraje','rTotalIVAS','rSubtotal','rValorTotalFactura','rPorcentajeDescuento','rValorDescuento','rPropina','rTotalICE','rValorTotalSinSubsidioECU','rAhorroPorSubsidioECU','rRecaudoSUIC','rTotalaPagar','nCodigoCara','nCodigoManguera','nIdVentaEstacion','rPuntosAcumulados','nFechaProximaRevicion','nTipoVenta','nTipoFactura','nTipoEmision','sIdentificacionConductor','sNombreConductor','nIdentPasaporte','nTotalFleet','sROM','nVentaCHIPIslero','nFacturarConductor','sBarCodeAutomotor','sTipoAuth','totalImpuestoFijo','modeSale','idArticuloDet','idTarifaIVADet','cantidadDet','valorUnitarioDet','porcentajeIVADet','porcentajeDescuentoDet','subtotalDet','valorIVADet','totalDet','valorDescuentoDet','codigoICEDet','porcentajeICEDet','valorICEDet','factorSubsidoECUDet','precioSinSubsidioECUDet','tipoIVADet','nCupo','nHoraTurnoActivo','nFechaZActiva','nSincronizaSICOM','nSincronizaSYSCOM','nNumeroTurno','nIdCentroVentaCons','nIdPuntoVentaCons','nIdentificacionEmpelado','sUsuarioFacturacion','sPassFacturacion','sIMEI','nFechaVenta','nHoraVenta','pNumeroFactura','pPrefijo','pCodigoElectronico','pNoValidarResolucion','pIdResolucion','pAnulada','pDescripcion','nRecaudo','sXMLDetCanastilla','tipoDescuento')
        return db.write([(invoice_operation_sql('invoice_fast_insert.sql'),
                          tuple(values.get(key) for key in keys))], result_model=SqlRow)

    def insert_invoice_conversion(**values):
        keys = ('idCompania','idCentroVenta','idPuntoVenta','idFacturaCliente',
                'identificacionCliente','nombreCliente','placa','tipoVenta',
                'codComprobante','kilometraje','isla')
        return station_flexible_write('invoice_conversion.sql', keys, **values)

    def invoice_rd(**values):
        keys = ('nIdCompania','nIdCentroVenta','nIdPuntoVenta','sCodComprobante',
                'nIdFc','sIdentificacionCL','sNombreCL','nIdCVCOn','nIDPVCON',
                'nIdResolucion','sNumeroFactura','sPrefijo','sCodElectronico',
                'sDescripcion','noValidaResolucion','anulada','nFacturada',
                'actualizaResolucion')
        return station_flexible_write('invoice_rd.sql', keys, **values)

    def insert_voided_payment(**values):
        keys = ('idVenta','idTurno','identificacionRed','codigoRespuestaActor',
                'mensajeRespuesta','secuencialTransaccion','numeroLote','horaTransaccion',
                'fechaTransaccion','numeroAutorizacion','tid','mid','valorInteres',
                'mensajeImpresion','codigoBanco','nombreBanco','nombreGrupoTarjeta',
                'modoLectura','nombreTarjetaHabiente','montoFijo','identificadorAplicacion',
                'aid','tipoCrigtograma','pin','arqc','numeroTarjetaTruncado',
                'fechaVencimientoTarjeta','numeroTarjetaEncriptada','impuesto',
                'baseConImpuesto','baseSinImpuesto','montoImpuesto','montoTotal',
                'idFormaPago','host','hostName','tipoTarjeta','tipoVenta','numeroTarjeta',
                'loteAbierto','nombreTH','aprobacion','idTerminal','numeroReferencia',
                'codigoReferencia','idComercio','diferidoyQuickPayment','reservado',
                'archivoFirma','tvr','tsi','anulada','sincronizada')
        return station_flexible_write('voided_payment_insert.sql', keys, **values)

    def flexible_write(filename, keys, result=False):
        def execute(**values):
            params = tuple(values.get(key) for key in keys)
            if result:
                return db.write([(invoice_operation_sql(filename), params)], result_model=SqlRow)
            count = db.write([(invoice_operation_sql(filename), params)], count_rows=True)
            return [SqlAffectedRows(affectedRows=count)]
        return execute

    def list_sales(*, ids):
        if not ids:
            return []
        xml = '<Ids>' + ''.join(f'<Id>{value}</Id>' for value in ids) + '</Ids>'
        return db.read(invoice_operation_sql('sales_by_codes.sql'), SaleCodeRow,
                       parameters=(xml, *invoice_station()))

    def lookup(filename, model, key):
        def execute(**values):
            return db.read(invoice_operation_sql(filename), model,
                           parameters=(values[key], *invoice_station()))
        return execute

    def insert_preset(*, cantidad, hora, cara, tipo, idTurno, producto):
        count = db.write([(invoice_operation_sql('insert_preset.sql'),
                          (cantidad, hora, cara, tipo, producto, idTurno, *invoice_station()))],
                         count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def preset_history(*, idTurno):
        return read_sql_row('preset_history_station.sql',
                            (idTurno, idTurno, *invoice_station()))

    def update_printer_width(*, codigoIsla, impresoraCaracteresNumero):
        island, company, center, _ = invoice_station()
        count = db.write([(invoice_operation_sql('update_printer_width.sql'),
                          (impresoraCaracteresNumero, codigoIsla, company, center))], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    return {
        'InsertarHistorialPreset': (PresetWrite, insert_preset),
        'ListarHistorialPresetsEstacion': (PresetFilter, preset_history),
        'ActualizarAnchoImpresionCapturador': (PrinterWidthWrite, update_printer_width),
        'ListarVentasPorCodigo': (InvoiceIds, list_sales),
        'ListarChecksVentasPorTurno': (DeliveryShift, lookup('sale_checks_by_shift.sql', SaleCheckRow, 'idTurno')),
        'ListarActasEntregaPorTurno': (DeliveryShift, lookup('deliveries_by_shift.sql', DeliveryRow, 'idTurno')),
        'ConsultarActaEntrega': (DeliveryId, lookup('delivery_by_id.sql', DeliveryRow, 'idActaEntrega')),
        'ListarDetallesActaEntrega': (DeliveryId, lookup('delivery_lines.sql', DeliveryLineRow, 'idActaEntrega')),
        'ListarFidelizacionPorFacturas': (InvoiceLoyaltyFilter, read_loyalty),
        'ListarPromocionesPorFacturas': (InvoiceIds, read_promotions),
        'ListarMovimientosFidelizacionPorTurno': (InvoiceLoyaltyMovementFilter, read_loyalty_movements),
        'ListarNotasCredito': (NoParameters, credit_notes),
        'ConsultarEstadoCaraVenta': (FaceShift, face_state),
        'ListarDetallesFormaPagoFactura': (PaymentDetailsFilter, payment_details),
        'ListarFacturasCambioFormaPago': (ShiftInvoicePayments, shift_invoice_payments),
        'ConsultarSiguienteCashbackTurno': (ShiftId, cashback_next),
        'ListarCashbacksTurno': (ShiftId, cashback_by_shift),
        'ConsultarCashbackTurno': (CashbackFilter, cashback_rows),
        'ConsultarValorCanjeUltimaVenta': (FaceOnly, canje),
        'ActualizarEstadoVentaCupo': (CreditSalesState, lambda **values: update_credit_sale('update_credit_sale.sql', **values)),
        'ActualizarEstadoTipoEnvioVentaCupo': (CreditSalesDeliveryState, lambda **values: update_credit_sale('update_credit_sale_delivery.sql', **values)),
        'ListarAutorizacionesPendientes': (AuthorizationPendingFilter, authorization_pending),
        'ProcesarAutorizacionPendiente': (AuthorizationPendingUpdate, authorization_pending_update),
        'ListarAutorizacionesExternas': (ExternalAuthorizationFilter, external_authorizations),
        'InsertarAutorizacionExterna': (ExternalAuthorizationWrite, external_authorization_insert),
        'ActualizarAutorizacionExterna': (ExternalAuthorizationUpdate, external_authorization_update),
        'ActualizarInventarioPuntoVenta': (InventoryUpdate, update_inventory),
        'InsertarCashbackTurno': (CashbackWrite, cashback_write),
        'ObtenerNumeroFactura': (InvoiceNumberRequest, invoice_number),
        'InsertarActaEntrega': (DeliveryCreate, delivery_create),
        'ActualizarFormaPagoDetalleAnulada': (VoidedPaymentUpdate, voided_payment_update),
        'EvaluarDescuentoVenta': (FlexibleParameters, evaluate_discount),
        'ActualizarDatosFacturaYCliente': (FlexibleParameters, update_invoice_customer),
        'InsertarCheckVentaEstacion': (FlexibleParameters, insert_sale_check),
        'InsertarVentaCupo': (FlexibleParameters, insert_credit_sale),
        'CrearFacturaRapida': (FlexibleParameters, insert_invoice_fast),
        'CrearConversionFacturaRapida': (FlexibleParameters, insert_invoice_conversion),
        'CrearFacturacionRdCompleta': (FlexibleParameters, invoice_rd),
        'InsertarFormaPagoDetalleAnulada': (FlexibleParameters, insert_voided_payment),
        'ConsultarNotaCreditoPorFactura': (InvoiceId, credit_note_exists),
        'InsertarNotaCreditoLocal': (CreditNoteWrite, insert_credit_note),
        'ActualizarCufeFactura': (InvoiceCufe, write('update_cufe.sql', 'cufe')),
        'ActualizarCufeConversion': (InvoiceCufe, write('update_conversion_cufe.sql', 'cufe')),
        'ObtenerConsecutivoVenta': (SaleSequence, sale_sequence),
        'ConsultarFacturasClienteCompletas': (CompleteInvoiceFilter, complete_invoice),
        'ConsultarFacturasCliente': (CompleteInvoiceFilter, invoice_headers),
        'ConsultarDetallesFacturaClienteCompletos': (InvoiceDetailSetsFilter, invoice_detail_sets),
        'GuardarResolucionFacturacion': (ResolutionWrite, save_resolution),
        'ListarDetallesFacturaCliente': (InvoiceIds, lines),
        'ActualizarXmlProcesoVenta': (SaleProcessXml, lambda **values: sale_xml('sale_xml.sql', **values)),
        'ActualizarXmlProcesoVentaCupo': (
            CreditSaleProcessXml, lambda **values: sale_xml('credit_sale_xml.sql', **values),
        ),
        'ActualizarEstadoCheckVenta': (SaleCheckState, set_sale_check),
        'ReactivarChecksVentasPendientes': (NoParameters, reset_pending_sales),
        'ConsultarFacturaAplicadaSorteo': (InvoiceId, raffle_state),
        'MarcarFacturaAplicadaSorteo': (InvoiceId, write('apply_raffle.sql')),
        'ActualizarFacturaFidelizada': (InvoiceLoyalty, write('update_loyalty.sql', 'fidelizada')),
        'ActualizarFacturaAnulada': (InvoiceVoided, write('void_invoice.sql', 'anulada')),
        'ActualizarEstadoFidelizacionFactura': (
            InvoiceLoyaltyState, write('update_loyalty_state.sql', 'state'),
        ),
    }
