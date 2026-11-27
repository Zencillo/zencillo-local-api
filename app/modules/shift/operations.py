from enum import Enum
from functools import cache
from importlib.resources import files
from typing import Annotated

from pydantic import BaseModel, Field

from app.core.database import SqlDatabase
from app.core.registry import Operation, request_actor
from app.errors import ApiError
from app.modules.article.operations import SqlAffectedRows
from app.schemas import NoParameters, SqlScalar, StrictModel


class ShiftQuery(Enum):
    SHIFT_BY_ID = "shift_by_id.sql"
    PENDING_SALES = "pending_sales.sql"
    FINAL_NOZZLE = "final_nozzle.sql"
    INITIAL_NOZZLE = "initial_nozzle.sql"
    OPEN_ZETA_DETAILS = "open_zeta_details.sql"
    OPEN_SHIFT_FOR_ZETA = "open_shift_for_zeta.sql"
    STATION_SCOPE = "station_scope.sql"
    MARK_INVOICING = "mark_invoicing.sql"
    DELETE_PRESETS = "delete_presets.sql"
    DELETE_ALL_PRESETS = "delete_all_presets.sql"
    CLOSE_SHIFT = "close_shift.sql"
    CLOSE_ZETA = "close_zeta.sql"
    OPEN_SHIFT = "open_shift.sql"
    OPEN_ZETA = "open_zeta.sql"
    INSERT_EXPENSE = "insert_shift_expense.sql"
    SHIFT_NOZZLE_READINGS = "shift_nozzle_readings.sql"
    INVENTORY_BALANCES = "inventory_balances.sql"
    SHIFT_EXPENSES = "shift_expenses.sql"
    ACM_CASH_BACK_TURNO_BD = "acm_cash_back_turno_bd.sql"
    ACM_DESCEUNTO_BD = "acm_desceunto_bd.sql"
    ACUMULADORA_ARTICULO_BD = "acumuladora_articulo_bd.sql"
    ACUMULADORA_FORMA_PAGO_BD = "acumuladora_forma_pago_bd.sql"
    INVOICE_COUNT = "invoice_count.sql"
    SPECIAL_SALE = "special_sale.sql"
    SPECIAL_DIFFERENCE = "special_difference.sql"
    SHIFT_BAGS = "shift_bags.sql"
    SPECIAL_DIFFERENCE_BY_HOSE = "special_difference_by_hose.sql"
    ISLAND_HAS_OPEN_SHIFT = "island_has_open_shift.sql"
    PRESET_HISTORY = "preset_history.sql"
    ZETA_FOLLOWUP = "zeta_followup.sql"
    SHIFTS_FOR_ZETA_FOLLOWUP = "shifts_for_zeta_followup.sql"
    OPEN_SHIFTS = "open_shifts.sql"
    SHIFTS_BY_ZETA = "shifts_by_zeta.sql"


@cache
def load_shift_query(query: ShiftQuery) -> str:
    if not isinstance(query, ShiftQuery):
        raise TypeError("Se requiere una consulta de turno registrada.")
    return files(__package__).joinpath("queries", query.value).read_text(encoding="utf8").strip()


SqlInt = Annotated[int, Field(ge=-2147483648, le=2147483647)]


class SalePoint(StrictModel):
    idPuntoVenta: SqlInt


class ShiftId(StrictModel):
    idTurno: SqlInt


class IslandCode(StrictModel):
    isla: SqlInt


class OpenShifts(StrictModel):
    islas: list[SqlInt] = Field(min_length=1, max_length=100)


class ShiftsByZeta(StrictModel):
    fechaZeta: str = Field(min_length=1, max_length=32)
    isla: int | None = None
    isOpen: bool = False


class OpenShiftExists(BaseModel):
    Abierto: int


class SpecialDifferenceByHose(BaseModel):
    IdManguera: SqlScalar
    Surtidor: SqlScalar
    Cara: SqlScalar
    Manguera: SqlScalar
    SubtotalReferencia: SqlScalar
    SubtotalReal: SqlScalar


class PresetHistory(BaseModel):
    IdHistorialPreset: SqlScalar
    Cantidad: SqlScalar
    Hora: SqlScalar
    Cara: SqlScalar
    Tipo: SqlScalar
    IdTurno: SqlScalar
    Producto: SqlScalar


class ZetaFollowup(BaseModel):
    IdJornadaZeta: SqlScalar
    Fecha: SqlScalar
    HoraApertura: SqlScalar
    HoraCierre: SqlScalar
    Abierta: SqlScalar
    SincronizoApertura: SqlScalar
    SincronizoCierre: SqlScalar
    SincronizoLecturasIniciales: SqlScalar
    SincronizoLecturasFinales: SqlScalar
    SincronizoTotalOperaciones: SqlScalar
    ManejaConsola: SqlScalar
    GuardaVariacion: SqlScalar
    CodCapturadorApertura: SqlScalar


class ZetaShiftFilter(IslandCode):
    fechaZeta: SqlInt


class ShiftForZetaFollowup(BaseModel):
    IdTurno: SqlScalar
    FechaZeta: SqlScalar
    Isla: SqlScalar
    Fecha: SqlScalar
    HoraApertura: SqlScalar
    HoraCierre: SqlScalar
    Abierto: SqlScalar
    Identificacion: SqlScalar
    SincronizoApertura: SqlScalar
    SincronizoCierre: SqlScalar
    NumeroDeTurno: SqlScalar
    SincronizoLecturasIniciales: SqlScalar
    SincronizoLecturasFinales: SqlScalar
    Empleado: SqlScalar


class InventoryBalance(BaseModel):
    CodigoArticulo: str | int | None
    Articulo: str | None
    NombreCorto: str | None
    saldo: int | float | None


class ShiftExpense(BaseModel):
    gasto: str | None
    total: int | float | None


class ShiftBag(BaseModel):
    IdTurno: int
    CodigoBolsa: str | int | None
    ValorBillete: int | float | None
    ValorMoneda: int | float | None
    Nota: str | None


class AcmCashBackTurnoBDRow(BaseModel):
    IdTurno: SqlScalar
    CodigoFP: SqlScalar
    Valor: SqlScalar
    Fee: SqlScalar
    Total: SqlScalar
    IdFormaPago: SqlScalar
    Nombre: SqlScalar
    Codigo: SqlScalar



class AcmDesceuntoBdRow(BaseModel):
    totaldescuento: SqlScalar
    tipo_descuento: SqlScalar



class AcumuladoraArticuloBDRow(BaseModel):
    IdTurno: SqlScalar
    CodigoArticulo: SqlScalar
    Calibracion: SqlScalar
    CodigoManguera: SqlScalar
    Articulo: SqlScalar
    Cantidad: SqlScalar
    Valor: SqlScalar
    Porcentaje: SqlScalar
    ValorUnitario: SqlScalar
    CantidadVentas: SqlScalar
    Combustible: SqlScalar



class AcumuladoraFormaPagoBDRow(BaseModel):
    NombreFormaPago: SqlScalar
    sum_Valor: SqlScalar
    Codigo: SqlScalar



class InvoiceCount(BaseModel):
    Cantidad: SqlScalar


class SpecialSale(BaseModel):
    VentaEspecial: SqlScalar


class SpecialDifference(BaseModel):
    total: SqlScalar


class ShiftNozzleReading(BaseModel):
    IdTurnoDetalle: SqlScalar
    IdTurno: SqlScalar
    IdManguera: SqlScalar
    LecturaInicial: SqlScalar
    LecturaFinal: SqlScalar
    LecturaDiferencia: SqlScalar
    Precio: SqlScalar
    Surtidor: SqlScalar
    Manguera: SqlScalar
    Articulo: SqlScalar
    Cara: SqlScalar
    IdCombustible: SqlScalar
    VolumenCalibracion: SqlScalar
    ValorCalibracion: SqlScalar
    CantidadVentasCalibracion: SqlScalar



class OpenZetaFilter(StrictModel):
    fecha: str | None = Field(default=None, pattern=r"^[0-9]{1,10}$")


class OpenZetaDetails(ZetaFollowup):
    XMLLecturaInicialTanques: SqlScalar
    XMLLecturaFinalTanques: SqlScalar
    Empleado: SqlScalar


class OpenShiftForZeta(StrictModel):
    fechaZeta: str = Field(pattern=r"^[0-9]{1,10}$")
    isla: int = Field(gt=0, le=2147483647)


class OpenShiftForZetaRow(BaseModel):
    IdTurno: SqlScalar
    FechaZeta: SqlScalar
    Isla: SqlScalar
    Fecha: SqlScalar
    HoraApertura: SqlScalar
    HoraCierre: SqlScalar
    Abierto: SqlScalar
    Identificacion: SqlScalar
    SincronizoApertura: SqlScalar
    SincronizoCierre: SqlScalar
    XMLApertura: SqlScalar
    XMLCierre: SqlScalar
    NumeroDeTurno: SqlScalar
    SincronizoLecturasIniciales: SqlScalar
    SincronizoLecturasFinales: SqlScalar
    Empleado: SqlScalar


class PendingSaleFilter(ShiftId):
    isla: int


class PendingSaleRow(BaseModel):
    IdVentaEstacion: SqlScalar
    Cara: SqlScalar
    Estado: SqlScalar
    IdTurno: SqlScalar
    IdDocumento: SqlScalar


class FinalNozzleParams(ShiftId):
    codigoManguera: int
    lectura: str = Field(pattern=r"^-?[0-9]+[.][0-9]{3}$")
    precio: str = Field(pattern=r"^-?[0-9]+[.][0-9]{7}$")


class InitialNozzleParams(ShiftId):
    codigoManguera: int
    lecturaValor: float
    precio: float


def shift_operations(db: SqlDatabase) -> dict[str, Operation]:
    def inventory_balances(*, idPuntoVenta: int):
        return db.read(load_shift_query(ShiftQuery.INVENTORY_BALANCES), InventoryBalance,
                       parameters=(idPuntoVenta,))

    def expenses(*, idTurno: int):
        return db.read(load_shift_query(ShiftQuery.SHIFT_EXPENSES), ShiftExpense,
                       parameters=(idTurno,))

    def bags(*, idTurno: int):
        return db.read(load_shift_query(ShiftQuery.SHIFT_BAGS), ShiftBag,
                       parameters=(idTurno,))

    def acm_cash_back_turno_bd(*, idTurno: int):
        return db.read(load_shift_query(ShiftQuery.ACM_CASH_BACK_TURNO_BD), AcmCashBackTurnoBDRow, parameters=(idTurno,))

    def acm_desceunto_bd(*, idTurno: int):
        return db.read(load_shift_query(ShiftQuery.ACM_DESCEUNTO_BD), AcmDesceuntoBdRow, parameters=(idTurno,))

    def acumuladora_articulo_bd(*, idTurno: int):
        return db.read(load_shift_query(ShiftQuery.ACUMULADORA_ARTICULO_BD), AcumuladoraArticuloBDRow, parameters=(idTurno,))

    def acumuladora_forma_pago_bd(*, idTurno: int):
        return db.read(load_shift_query(ShiftQuery.ACUMULADORA_FORMA_PAGO_BD), AcumuladoraFormaPagoBDRow, parameters=(idTurno,))

    def invoice_count(*, idTurno: int):
        return db.read(load_shift_query(ShiftQuery.INVOICE_COUNT), InvoiceCount, parameters=(idTurno,))

    def special_sale(*, idTurno: int):
        return db.read(load_shift_query(ShiftQuery.SPECIAL_SALE), SpecialSale, parameters=(idTurno,))

    def special_difference(*, idTurno: int):
        return db.read(load_shift_query(ShiftQuery.SPECIAL_DIFFERENCE), SpecialDifference, parameters=(idTurno,))

    def shift_nozzle_readings(*, idTurno: int):
        return db.read(load_shift_query(ShiftQuery.SHIFT_NOZZLE_READINGS), ShiftNozzleReading, parameters=(idTurno,))

    def differences_by_hose(*, idTurno: int):
        return db.read(load_shift_query(ShiftQuery.SPECIAL_DIFFERENCE_BY_HOSE),
                       SpecialDifferenceByHose, parameters=(idTurno,))

    def island_has_open_shift(*, isla: int):
        return db.read(load_shift_query(ShiftQuery.ISLAND_HAS_OPEN_SHIFT), OpenShiftExists,
                       parameters=(isla,))

    def preset_history(*, idTurno: int):
        return db.read(load_shift_query(ShiftQuery.PRESET_HISTORY), PresetHistory,
                       parameters=(idTurno,))

    def list_zeta_followup():
        return db.read(load_shift_query(ShiftQuery.ZETA_FOLLOWUP), ZetaFollowup)

    def list_shifts_for_zeta_followup(*, fechaZeta: int, isla: int):
        return db.read(load_shift_query(ShiftQuery.SHIFTS_FOR_ZETA_FOLLOWUP),
                       ShiftForZetaFollowup, parameters=(fechaZeta, isla))

    def open_zeta_details(*, fecha):
        return db.read(load_shift_query(ShiftQuery.OPEN_ZETA_DETAILS), OpenZetaDetails,
                       parameters=(fecha, fecha))

    def open_shift_for_zeta(*, fechaZeta, isla):
        station, _ = request_actor.get()
        if station.rsplit('/', 1)[-1] != str(isla):
            raise ApiError(403, 'STATION_MISMATCH', 'Isla no autorizada')
        return db.read(load_shift_query(ShiftQuery.OPEN_SHIFT_FOR_ZETA), OpenShiftForZetaRow,
                       parameters=(fechaZeta, isla))

    def scoped_island():
        station, _ = request_actor.get()
        try:
            return int(station.rsplit('/', 1)[-1])
        except ValueError:
            raise ApiError(403, 'INVALID_STATION', 'Perfil de estación inválido') from None

    def shift_by_id(*, idTurno):
        return db.read(load_shift_query(ShiftQuery.SHIFT_BY_ID), OpenShiftForZetaRow,
                       parameters=(idTurno, scoped_island()))

    def pending_sales(*, idTurno, isla):
        if isla != scoped_island():
            raise ApiError(403, 'STATION_MISMATCH', 'Isla no autorizada')
        return db.read(load_shift_query(ShiftQuery.PENDING_SALES), PendingSaleRow,
                       parameters=(idTurno, isla))

    def final_nozzle(*, idTurno, codigoManguera, lectura, precio):
        count = db.write([(load_shift_query(ShiftQuery.FINAL_NOZZLE),
                          (idTurno, scoped_island(), idTurno, codigoManguera, lectura, precio))],
                        count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def initial_nozzle(*, idTurno, codigoManguera, lecturaValor, precio):
        count = db.write([(load_shift_query(ShiftQuery.INITIAL_NOZZLE),
                          (idTurno, scoped_island(), idTurno, codigoManguera, lecturaValor, precio))],
                        count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def open_shifts(*, islas):
        marks = ", ".join("?" for _ in islas)
        sql = load_shift_query(ShiftQuery.OPEN_SHIFTS).replace("{{ISLAS}}", marks)
        return db.read(sql, parameters=tuple(islas))

    def delete_all_presets():
        count = db.write(
            [(load_shift_query(ShiftQuery.DELETE_ALL_PRESETS), ())],
            count_rows=True,
        )
        return [SqlAffectedRows(affectedRows=count)]

    def shifts_by_zeta(*, fechaZeta, isla, isOpen):
        return db.read(
            load_shift_query(ShiftQuery.SHIFTS_BY_ZETA),
            parameters=(fechaZeta, isla, isla, 1 if isOpen else 0),
        )

    return {
        "ConsultarTurnoEmpleadoPorId": (ShiftId, shift_by_id),
        "ListarVentasPendientesPorTurno": (PendingSaleFilter, pending_sales),
        "GuardarLecturaFinalTurnoDetalle": (FinalNozzleParams, final_nozzle),
        "GuardarLecturaInicialTurnoDetalle": (InitialNozzleParams, initial_nozzle),
        "ConsultarZetaAbierta": (OpenZetaFilter, open_zeta_details),
        "ConsultarTurnoAbiertoPorZeta": (OpenShiftForZeta, open_shift_for_zeta),
        "ListarJornadasZetaSeguimiento": (NoParameters, list_zeta_followup),
        "ListarTurnosZetaSeguimiento": (ZetaShiftFilter, list_shifts_for_zeta_followup),
        "ListarHistorialPresetsTurno": (ShiftId, preset_history),
        "ListarDiferenciasPrecioEspecialTurno": (ShiftId, differences_by_hose),
        "ConsultarExisteTurnoAbiertoIsla": (IslandCode, island_has_open_shift),
        "ListarLecturasMangueraTurno": (ShiftId, shift_nozzle_readings),
        "ConsultarDiferenciaVentaEspecialTurno": (ShiftId, special_difference),
        "ConsultarVentaEspecialTurno": (ShiftId, special_sale),
        "ContarFacturasTurno": (ShiftId, invoice_count),
        "ListarFormasPagoAcumuladasTurno": (ShiftId, acumuladora_forma_pago_bd),
        "ListarArticulosAcumuladosTurno": (ShiftId, acumuladora_articulo_bd),
        "ListarDescuentosAcumuladosTurno": (ShiftId, acm_desceunto_bd),
        "ListarCashbackAcumuladoTurno": (ShiftId, acm_cash_back_turno_bd),
        "ListarExistenciasPuntoVenta": (SalePoint, inventory_balances),
        "ListarGastosAcumuladosTurno": (ShiftId, expenses),
        "ListarBolsasAcumuladasTurno": (ShiftId, bags),
        "ListarTurnosAbiertos": (OpenShifts, open_shifts),
        "ListarTurnosPorZeta": (ShiftsByZeta, shifts_by_zeta),
        "EliminarHistorialPresets": (NoParameters, delete_all_presets),
    }


class ShiftExpenseInsert(StrictModel):
    idcompania: int = Field(ge=-2147483648, le=2147483647)
    idturno: int = Field(ge=-2147483648, le=2147483647)
    idgastotipo: int = Field(ge=-2147483648, le=2147483647)
    valor: float = Field(allow_inf_nan=False)
    descripcion: str = Field(max_length=8000)
    numerofactura: str = Field(max_length=8000)
    sincronizado: int = Field(ge=-2147483648, le=2147483647)


def shift_expense_operation(db: SqlDatabase, guard: str) -> dict[str, Operation]:
    def insert(*, idcompania, idturno, idgastotipo, valor, descripcion, numerofactura, sincronizado):
        station, _ = request_actor.get()
        if station != '900716/10370/1' or idcompania != 900716:
            raise ApiError(403, 'STATION_MISMATCH', 'Estación no autorizada para el piloto')
        count = db.write([(guard, ()), (load_shift_query(ShiftQuery.INSERT_EXPENSE),
                          (idcompania, idturno, idgastotipo, valor, descripcion, numerofactura, sincronizado,
                           idturno, 1))], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    return {'InsertarGastoTurno': (ShiftExpenseInsert, insert)}


class ShiftOpenZetaParams(StrictModel):
    fecha: str = Field(max_length=64000)
    horaApertura: str = Field(max_length=64000)
    abierta: int = Field(ge=-2147483648, le=2147483647)
    sincronizoApertura: int = Field(ge=-2147483648, le=2147483647)
    sincronizoCierre: int = Field(ge=-2147483648, le=2147483647)
    sincronizoLecturasIniciales: int = Field(ge=-2147483648, le=2147483647)
    sincronizoLecturasFinales: int = Field(ge=-2147483648, le=2147483647)
    sincronizoTotalOperaciones: int = Field(ge=-2147483648, le=2147483647)
    empleado: str = Field(max_length=64000)
    contrasenaEmpleado: str = Field(max_length=64000)
    manejaConsola: int = Field(ge=-2147483648, le=2147483647)
    guardaVariacion: int = Field(ge=-2147483648, le=2147483647)
    codCapturadorApertura: str = Field(max_length=64000)


class ShiftOpenShiftParams(StrictModel):
    fechaZeta: str = Field(max_length=64000)
    isla: int = Field(ge=-2147483648, le=2147483647)
    fecha: str = Field(max_length=64000)
    horaApertura: str = Field(max_length=64000)
    horaCierre: str = Field(max_length=64000)
    abierto: int = Field(ge=-2147483648, le=2147483647)
    identificacion: str = Field(max_length=64000)
    sincronizoApertura: int = Field(ge=-2147483648, le=2147483647)
    sincronizoCierre: int = Field(ge=-2147483648, le=2147483647)
    sincronizoLecturasIniciales: int = Field(ge=-2147483648, le=2147483647)
    sincronizoLecturasFinales: int = Field(ge=-2147483648, le=2147483647)
    sincronizoTotalOperaciones: int = Field(ge=-2147483648, le=2147483647)
    empleado: str = Field(max_length=64000)
    contrasenaEmpleado: str = Field(max_length=64000)
    xMLApertura: str = Field(max_length=64000)


class ShiftCloseZetaParams(StrictModel):
    abierta: int = Field(ge=-2147483648, le=2147483647)
    idJornadaZeta: int = Field(ge=-2147483648, le=2147483647)
    horaCierre: str = Field(max_length=64000)


class ShiftCloseShiftParams(StrictModel):
    idTurno: int = Field(ge=-2147483648, le=2147483647)
    horaCierre: str = Field(max_length=64000)
    fechaCierre: str = Field(max_length=64000)
    xMLCierre: str | None = Field(default=None, max_length=64000)


class ShiftDeletePresetsParams(StrictModel):
    idTurno: int = Field(ge=-2147483648, le=2147483647)


class ShiftMarkInvoicingParams(StrictModel):
    idTurno: int = Field(ge=-2147483648, le=2147483647)


def shift_statement_operations(db: SqlDatabase, guard: str) -> dict[str, Operation]:
    def write(query, keys):
        def execute(**values):
            station, _ = request_actor.get()
            try:
                company, center, island = (int(part) for part in station.split('/'))
            except ValueError:
                raise ApiError(403, 'INVALID_STATION', 'Perfil de estación inválido') from None
            if 'isla' in values and values['isla'] != island:
                raise ApiError(403, 'STATION_MISMATCH', 'Estación no autorizada para el piloto')
            args = tuple(values[key] for key in keys)
            if query in (ShiftQuery.CLOSE_SHIFT, ShiftQuery.DELETE_PRESETS, ShiftQuery.MARK_INVOICING):
                args += (island,)
            count = db.write([
                (guard, ()),
                (load_shift_query(ShiftQuery.STATION_SCOPE), (company, center, island)),
                (load_shift_query(query), args),
            ], count_rows=True)
            return [SqlAffectedRows(affectedRows=count)]
        return execute

    return {
        'AbrirJornadaZeta': (ShiftOpenZetaParams, write(ShiftQuery.OPEN_ZETA, ('fecha', 'horaApertura', 'abierta', 'sincronizoApertura', 'sincronizoCierre', 'sincronizoLecturasIniciales', 'sincronizoLecturasFinales', 'sincronizoTotalOperaciones', 'empleado', 'contrasenaEmpleado', 'manejaConsola', 'guardaVariacion', 'codCapturadorApertura'))),
        'AbrirTurnoEmpleado': (ShiftOpenShiftParams, write(ShiftQuery.OPEN_SHIFT, ('fechaZeta', 'isla', 'fecha', 'horaApertura', 'horaCierre', 'abierto', 'identificacion', 'sincronizoApertura', 'sincronizoCierre', 'fecha', 'isla', 'sincronizoLecturasIniciales', 'sincronizoLecturasFinales', 'sincronizoTotalOperaciones', 'empleado', 'contrasenaEmpleado', 'xMLApertura'))),
        'CerrarJornadaZeta': (ShiftCloseZetaParams, write(ShiftQuery.CLOSE_ZETA, ('abierta', 'horaCierre', 'idJornadaZeta'))),
        'CerrarTurnoEmpleado': (ShiftCloseShiftParams, write(ShiftQuery.CLOSE_SHIFT, ('horaCierre', 'xMLCierre', 'xMLCierre', 'fechaCierre', 'idTurno'))),
        'EliminarHistorialPresetTurno': (ShiftDeletePresetsParams, write(ShiftQuery.DELETE_PRESETS, ('idTurno',))),
        'MarcarFacturacionTurnoEmpleado': (ShiftMarkInvoicingParams, write(ShiftQuery.MARK_INVOICING, ('idTurno',))),
    }
