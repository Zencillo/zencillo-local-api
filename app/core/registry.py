from collections.abc import Callable, Mapping
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from types import MappingProxyType
from contextvars import ContextVar

from pydantic import BaseModel, ValidationError

from app.config import Device
from app.core.database import request_context
from app.errors import ApiError
from app.schemas import OperationRequest


request_actor: ContextVar[tuple[str, str]] = ContextVar('request_actor')

# SQL connection/licensing and employee secrets never leave the station API.
# This is column based, not an operation/result projection: all other query
# columns stay untouched for Flutter's existing converters.
_PRIVATE_COLUMNS = frozenset({
    "clave", "claveturno", "contrasenalicencia", "usuariolicencia",
    "contrasenapinpad", "contrasenaempleadoturno", "password", "sqlpassword",
})


type Operation = tuple[type[BaseModel], Callable[..., object]]


class Operations:
    def __init__(self, registry: Mapping[str, Operation]):
        self.registry = MappingProxyType(dict(registry))

    def run(self, request: OperationRequest, device: Device, request_id: str, device_id: str) -> dict:
        operation = self.registry.get(request.Query)
        if operation is None:
            raise ApiError(404, "OPERATION_NOT_FOUND", "Operación desconocida")
        if request.Query not in device.operations:
            raise ApiError(403, "FORBIDDEN", "Operación no autorizada")
        schema, handler = operation
        try:
            parameters = schema.model_validate(request.parameters)
        except ValidationError as exc:
            raise ApiError(400, "INVALID_PARAMETERS", "Parámetros inválidos") from exc
        token = request_context.set((request_id, request.Query))
        actor = request_actor.set((device.station, device_id))
        try:
            result = handler(**parameters.model_dump())
            items = result if isinstance(result, list) else [result]
            return {"items": [_to_json(item) for item in items]}
        finally:
            request_actor.reset(actor)
            request_context.reset(token)


def _to_json(value):
    """Return raw registered-SQL values without result projections."""
    # El driver SQL directo de Capturador expone BIT como 1/0. Conservamos
    # ese contrato para los modelos Dart que reciben enteros de configuración.
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, BaseModel):
        return _to_json(value.model_dump(mode="python"))
    if isinstance(value, Mapping):
        return {
            str(key): _to_json(item)
            for key, item in value.items()
            if str(key).casefold() not in _PRIVATE_COLUMNS
        }
    if isinstance(value, (list, tuple)):
        return [_to_json(item) for item in value]
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Enum):
        return _to_json(value.value)
    return value
