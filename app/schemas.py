from datetime import date, datetime, time
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, SecretStr, StrictFloat, StrictInt, StrictStr


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Login(StrictModel):
    device_id: str = Field(min_length=1, max_length=128)
    secret: SecretStr = Field(min_length=1, max_length=512)
    licenseCompany: str | None = Field(default=None, min_length=1, max_length=32)
    licenseUser: str | None = Field(default=None, min_length=1, max_length=256)
    licensePassword: SecretStr | None = Field(default=None, min_length=1, max_length=512)


class LicenseBootstrap(StrictModel):
    pass


class DeviceLicenseLogin(StrictModel):
    device_id: str = Field(min_length=1, max_length=128)
    licenseCompany: str = Field(min_length=1, max_length=32)
    licenseUser: str = Field(min_length=1, max_length=256)
    licensePassword: SecretStr = Field(min_length=1, max_length=512)


class SqlLogin(Login):
    sqlUser: str = Field(min_length=1, max_length=128)
    sqlPassword: SecretStr = Field(min_length=1, max_length=512)


class OperationRequest(StrictModel):
    Query: str = Field(min_length=1, max_length=80)
    parameters: dict


class NoParameters(StrictModel):
    pass


def sql_scalar(value):
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, Decimal):
        return float(value)
    return value


# SQL installations can store the same legacy setting as text or a number.
SqlScalar = Annotated[
    StrictInt | StrictStr | StrictFloat | datetime | date | time | None,
    BeforeValidator(sql_scalar),
]


class WriteResult(BaseModel):
    applied: bool = True
