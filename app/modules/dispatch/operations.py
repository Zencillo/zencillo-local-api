from enum import Enum
from functools import cache
from importlib.resources import files

from pydantic import BaseModel, Field

from app.core.database import SqlDatabase
from app.modules.article.operations import SqlAffectedRows
from app.core.registry import Operation, request_actor
from app.errors import ApiError
from app.schemas import NoParameters, SqlScalar, StrictModel


class DispatchQuery(Enum):
    REGISTER = "register_dispatch.sql"
    CANCEL = "cancel_dispatch.sql"
    CLIENTS = "client_dispatches.sql"
    PENDING = "pending_dispatches.sql"


@cache
def load_dispatch_query(query: DispatchQuery) -> str:
    if not isinstance(query, DispatchQuery):
        raise TypeError("Se requiere una consulta de despacho registrada.")
    return files(__package__).joinpath("queries", query.value).read_text(encoding="utf8").strip()


class ClientDispatch(BaseModel):
    idpredespachocliente: SqlScalar
    bono_premio: SqlScalar
    cara: SqlScalar
    identificacion: SqlScalar
    nombre: SqlScalar
    estado: SqlScalar
    fechacreacion: SqlScalar
    fechamodificacion: SqlScalar
    idturno: SqlScalar
    descuento: SqlScalar


class PendingDispatchFilter(StrictModel):
    idTurno: int = Field(ge=-2147483648, le=2147483647)
    cara: int | None = Field(default=None, ge=-2147483648, le=2147483647)


class PendingDispatch(BaseModel):
    IdVentaEstacion: SqlScalar
    FormaPago: SqlScalar
    Fecha: SqlScalar
    CodigoCara: SqlScalar
    IdentificacionCliente: SqlScalar
    NombreCliente: SqlScalar
    ValorVenta: SqlScalar
    VolumenVenta: SqlScalar
    ValorUnitario: SqlScalar
    CodigoManguera: SqlScalar
    Placa: SqlScalar


class DispatchCancellation(StrictModel):
    idPredespachoCliente: int = Field(gt=0, le=2147483647)


class DispatchRegistration(StrictModel):
    cara: int = Field(ge=1, le=2147483647)
    identificacion: str
    nombreCliente: str
    descuento: float
    usaBonoPremio: bool
    formaPago: str


def dispatch_operations(db: SqlDatabase) -> dict[str, Operation]:
    def clients():
        return db.read(load_dispatch_query(DispatchQuery.CLIENTS), ClientDispatch)

    def pending(*, idTurno: int, cara: int | None):
        return db.read(load_dispatch_query(DispatchQuery.PENDING), PendingDispatch,
                       parameters=(idTurno, cara, cara))

    def cancel(*, idPredespachoCliente: int):
        station, _ = request_actor.get()
        try:
            company, center, island = (int(part) for part in station.split('/'))
        except ValueError:
            raise ApiError(403, 'INVALID_STATION', 'Perfil de estación inválido') from None
        count = db.write([(load_dispatch_query(DispatchQuery.CANCEL),
                          (idPredespachoCliente, company, center, island))], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def register(*, cara, identificacion, nombreCliente, descuento, usaBonoPremio, formaPago):
        station, _ = request_actor.get()
        try:
            company, center, island = (int(part) for part in station.split('/'))
        except ValueError:
            raise ApiError(403, 'INVALID_STATION', 'Perfil de estación inválido') from None
        count = db.write([(load_dispatch_query(DispatchQuery.REGISTER),
                   (cara, island, company, center, cara, identificacion, nombreCliente,
                    descuento, int(usaBonoPremio), formaPago))], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    return {
        "RegistrarPredespachoCliente": (DispatchRegistration, register),
        "CancelarPredespachoCliente": (DispatchCancellation, cancel),
        "ListarPredespachosClientes": (NoParameters, clients),
        "ListarPredespachosPendientes": (PendingDispatchFilter, pending),
    }
