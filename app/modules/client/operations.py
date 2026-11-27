from importlib.resources import files

from pydantic import BaseModel, Field

from app.core.database import SqlDatabase
from app.core.registry import Operation
from app.schemas import SqlScalar, StrictModel, WriteResult


QUERY_NAMES = (
    "client_by_id.sql", "client_by_plate.sql", "client_by_tag.sql", "lock_client.sql", "upsert_client.sql",
    "credit_contract.sql", "upsert_plate.sql", "guard_plate.sql",
)


def load_client_queries():
    directory = files(__package__).joinpath("queries")
    return tuple(directory.joinpath(name).read_text(encoding="utf8") for name in QUERY_NAMES)


class ClientKey(StrictModel):
    key: str = Field(min_length=1, max_length=100)


class ClientFields(BaseModel):
    Identificacion: SqlScalar
    NombreCliente: SqlScalar
    IdGrupoEmpresarial: SqlScalar
    GrupoEmpresarial: SqlScalar
    Telefono: SqlScalar
    ClienteCorreo: SqlScalar
    DigVef: SqlScalar
    tipoIntegracion: SqlScalar


class ClientIdentification(ClientFields):
    Verificado: SqlScalar
    CodTipo: SqlScalar


class ClientPlate(ClientIdentification):
    Placa: SqlScalar


class ClientTag(ClientFields):
    Placa: SqlScalar
    Identificador: SqlScalar


class ClientUpsert(StrictModel):
    identificacion: str = Field(min_length=1, max_length=50)
    nombreCliente: str | None = Field(default=None, max_length=200)
    idGrupoEmpresarial: str | None = Field(default=None, max_length=50)
    grupoEmpresarial: str | None = Field(default=None, max_length=200)
    telefono: str | None = Field(default=None, max_length=50)
    correo: str | None = Field(default=None, max_length=200)
    digVef: str | None = Field(default=None, max_length=5)
    verificado: int | None = Field(default=None, ge=0, le=1)
    codTipo: str | None = Field(default=None, max_length=50)


class CreditContract(BaseModel):
    idcontratocredito: SqlScalar
    idcliente: SqlScalar
    identificacion: SqlScalar
    cliente: SqlScalar
    fechainicio: SqlScalar
    fechafin: SqlScalar
    descripcion: SqlScalar
    numero: SqlScalar


def client_operations(db: SqlDatabase) -> dict[str, Operation]:
    identification, plate, tag, _, _, contract, _, _ = load_client_queries()

    def by_identification(*, key: str):
        return db.read(identification, ClientIdentification, parameters=(key,))

    def by_plate(*, key: str):
        return db.read(plate, ClientPlate, parameters=(key,))

    def by_tag(*, key: str):
        return db.read(tag, ClientTag, parameters=(key,))

    def by_contract(*, key: str):
        return db.read(contract, CreditContract, parameters=(key,))

    return {
        "ConsultarContratoCreditoLocal": (ClientKey, by_contract),
        "ConsultarClienteOffline": (ClientKey, by_identification),
        "ConsultarClienteOfflinePorPlaca": (ClientKey, by_plate),
        "ConsultarClienteOfflinePorIdentificador": (ClientKey, by_tag),
    }


class PlateUpsert(StrictModel):
    placa: str = Field(max_length=20)
    identificadorPlaca: str = Field(max_length=20)
    identificacion: str = Field(max_length=50)
    correoPlaca: str = Field(max_length=50)


def client_write_operations(db: SqlDatabase) -> dict[str, Operation]:
    _, _, _, lock, upsert, _, plate, guard_plate = load_client_queries()

    def save(*, identificacion, nombreCliente, idGrupoEmpresarial, grupoEmpresarial,
             telefono, correo, digVef, verificado, codTipo):
        db.write((
            (lock, (identificacion,)),
            (upsert, (identificacion, nombreCliente or None, idGrupoEmpresarial or None,
                      grupoEmpresarial or None, telefono or None, correo or None, digVef or None,
                      verificado, codTipo or None)),
        ))
        return [WriteResult()]

    def save_plate(*, placa: str, identificadorPlaca: str, identificacion: str, correoPlaca: str):
        db.write((
            (guard_plate, (placa,)),
            (plate, (placa, identificadorPlaca, identificacion, correoPlaca)),
        ))
        return [WriteResult()]

    return {
        "GuardarClienteOffline": (ClientUpsert, save),
        "GuardarPlacaOffline": (PlateUpsert, save_plate),
    }
