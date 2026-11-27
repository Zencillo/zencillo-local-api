from decimal import Decimal
from importlib.resources import files

from pydantic import BaseModel, Field

from app.core.database import SqlDatabase
from app.core.registry import Operation, request_actor
from app.errors import ApiError
from app.modules.article.operations import SqlAffectedRows
from app.schemas import SqlScalar, StrictModel, WriteResult


def load_price_queries():
    queries = files(__package__).joinpath("queries")
    return tuple(queries.joinpath(name).read_text(encoding="utf8")
                 for name in ("scheduled_prices.sql", "manual_price_history.sql"))


class ManualHistoryFilter(StrictModel):
    codigoIsla: int = Field(ge=-2147483648, le=2147483647)


class ScheduledPricesFilter(ManualHistoryFilter):
    fecha: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}$")
    aplicado: int = Field(ge=0, le=1)
    horaInicio: int = Field(ge=-2147483648, le=2147483647)
    horaFin: int = Field(ge=-2147483648, le=2147483647)


class ScheduledPrice(BaseModel):
    IdArticuloPrecioProgramado: SqlScalar
    CodigoIsla: SqlScalar
    IdManguera: SqlScalar
    CodigoManguera: SqlScalar
    Precio1: SqlScalar
    Precio2: SqlScalar
    Precio3: SqlScalar
    Precio4: SqlScalar
    Fecha: SqlScalar
    HoraInicio: SqlScalar
    HoraFin: SqlScalar
    Aplicado: SqlScalar


class ManualPrice(BaseModel):
    IdArticuloPrecioProgramadoManual: SqlScalar
    IdentificacionEmpleado: SqlScalar
    CodigoIsla: SqlScalar
    IdManguera: SqlScalar
    CodigoManguera: SqlScalar
    Precio: SqlScalar
    FechaEnviado: SqlScalar
    Aplicado: SqlScalar
    Nombre: SqlScalar


class ScheduledPriceUpdate(StrictModel):
    codigoIsla: str = Field(pattern=r"^[0-9]{1,10}$")
    codigoManguera: str
    precio1: float
    precio2: float
    precio3: float
    precio4: float
    fecha: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$")
    horaInicio: str
    horaFin: str
    aplicado: bool
    idArticuloPrecioProgramado: int = Field(ge=-2147483648, le=2147483647)


def price_operations(db: SqlDatabase) -> dict[str, Operation]:
    schedule, history = load_price_queries()

    def scheduled(*, fecha, aplicado, horaInicio, horaFin, codigoIsla):
        return db.read(schedule, ScheduledPrice, parameters=(fecha, aplicado, horaInicio, horaFin, codigoIsla))

    def manual(*, codigoIsla):
        return db.read(history, ManualPrice, parameters=(codigoIsla,))

    def update_scheduled(**values):
        station, _ = request_actor.get()
        try:
            company, center, island = (int(part) for part in station.split('/'))
        except ValueError:
            raise ApiError(403, 'INVALID_STATION', 'Perfil de estación inválido') from None
        if int(values['codigoIsla']) != island:
            raise ApiError(403, 'STATION_MISMATCH', 'Isla no autorizada')
        keys = ('codigoIsla', 'codigoManguera', 'precio1', 'precio2', 'precio3', 'precio4',
                'fecha', 'horaInicio', 'horaFin', 'aplicado', 'idArticuloPrecioProgramado')
        sql = files(__package__).joinpath('queries', 'update_scheduled_price.sql').read_text(encoding='utf8')
        count = db.write([(sql, (*(values[key] for key in keys), island, company, center, island))],
                         count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def update_hose(*, idManguera: int, precio: str):
        count = db.write([(
            "UPDATE MangueraTanque SET Precio = ? WHERE IdManguera = ?",
            (Decimal(precio), idManguera),
        )], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    return {
        "ActualizarPrecioProgramado": (ScheduledPriceUpdate, update_scheduled),
        "ActualizarPrecioMangueraTanque": (HosePriceUpdate, update_hose),
        "ListarPreciosProgramados": (ScheduledPricesFilter, scheduled),
        "ListarHistorialPreciosManuales": (ManualHistoryFilter, manual),
    }


class HosePriceUpdate(StrictModel):
    idManguera: int = Field(ge=-2147483648, le=2147483647)
    precio: str = Field(max_length=48, pattern=r"^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]{1,3})?$")


class ManualPriceEntry(ManualHistoryFilter):
    idManguera: int = Field(ge=-2147483648, le=2147483647)
    codigoManguera: str = Field(pattern=r"^[+-]?[0-9]{1,10}$")
    precio: str = Field(max_length=48, pattern=r"^[+-]?[0-9]+([.][0-9]+)?([eE][+-]?[0-9]{1,3})?$")
    fechaEnviado: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$")
    aplicado: bool
    identificacionEmpleado: str = Field(max_length=15)


def laboratory_price_write_operations(db: SqlDatabase) -> dict[str, Operation]:
    """Kept outside the station registry until its identity side effect can be validated."""
    insert_sql = files(__package__).joinpath("queries", "insert_manual_price.sql").read_text(encoding="utf8")

    def add_manual(*, codigoIsla, idManguera, codigoManguera, precio, fechaEnviado,
                   aplicado, identificacionEmpleado):
        bindings = (codigoIsla, idManguera, codigoManguera, Decimal(precio), fechaEnviado,
                    int(aplicado), identificacionEmpleado)
        db.write(((insert_sql, bindings),))
        return [WriteResult()]

    return {"RegistrarHistorialPrecioManual": (ManualPriceEntry, add_manual)}
