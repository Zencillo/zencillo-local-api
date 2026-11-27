from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas import StrictModel


class VehicleType(BaseModel):
    idtipovehiculo: int | None
    tipovehiculo: str | None


class ExpenseType(BaseModel):
    idcompania: int
    idgastotipo: int
    gastotipo: str | None
    contabilidadcuenta: str | None
    estado: int
    fechacreacion: datetime | None
    fechamodificacion: datetime | None
    fechaultimomovimiento: datetime | None


class RoundingConfig(BaseModel):
    Documento: int | str | None
    Posicion: int | None
    Descripcion: str | None
    AplicaRedondeo: int | None
    FactorRedondeo: int | float | None


class Fuel(BaseModel):
    IdCombustible: int
    IdArticulo: int | None
    Color: str | None
    Nombre: str | None
    CodigoArticulo: str | None


class FuelByFace(BaseModel):
    IdCara: int | None
    IdCombustible: int | None
    IdArticuloCombustible: int | None
    Nombre: str | None
    Precio: str | float | None
    Color: str | None
    CodigoCara: int | str | None
    CodigoManguera: int | str | None
    CodigoCombustible: str | int | None
    IdManguera: int | None
    IdArticulo: int | None
    IdTarifaIVA: int | None
    IdPresentacion: int | None
    CodigoArticulo: str | int | None
    CodigoAlterno: str | int | None
    PrecioAbierto: int | None
    IncluyeIVA: int | None
    Articulo: str | None
    NombreCorto: str | None
    PrecioArticulo: float | None
    Presentacion: str | None
    PresentacionUnidades: int | str | None
    Porcentaje: int | float | None
    CodigoICE: int | str | None
    PorcentajeICE: int | float | None
    Combustible: int | None
    Estado: int | None
    ImpuestoValorFijo: float | None
    imprimir_nombre_corto: int | None


class IslandCode(StrictModel):
    codigoIsla: str = Field(min_length=1, max_length=40)


class FaceFilters(StrictModel):
    gnIsla: int = Field(ge=-2147483648, le=2147483647)
    gnNumeroCapturador: int = Field(ge=-2147483648, le=2147483647)
    isMultiIsla: bool


class Hose(BaseModel):
    IdManguera: int | None
    CodigoManguera: int | str | None
    Descripcion: str | None
    Grado: int | str | None
    IdTanque: int | None
    Tanque: str | int | None
    IdCombustible: int | None
    IdCara: int | None
    IdLector: int | None
    IdCentroVentaLectores: int | None
    Precio: str | float | None
    CantidadDecimalesPrecio: int | None
    NumeroProducto: int | None


class Face(BaseModel):
    IdCara: int | None
    CodigoCara: int | str | None
    ModoCara: str | int | None
    Descripcion: str | None
    IdSurtidor: int | None
    CodigoSurtidor: int | str | None
    IdIsla: int | None
    CodigoIsla: int | str | None
    POS: str | int | None
    Totalizadores: int | None
    NumeroCapturador: int | None


class FaceWithHose(BaseModel):
    IdIsla: int | None
    CodigoIsla: int | str | None
    IdSurtidor: int | None
    CodigoSurtidor: int | str | None
    ModoCara: str | int | None
    IdCara: int | None
    CodigoCara: int | str | None
    CodigoManguera: int | str | None
    IdManguera: int | None
    IdCombustible: int | None
    Descripcion: str | None
    IdArticulo: int | None
    Articulo: str | None
    CodigoArticulo: str | int | None
    Precio: str | float | None


class EcuadorSubsidy(BaseModel):
    IdArticulo: int | None
    SubsidioFactor: float | None
    Ano: int | None
    Mes: int | None


class PaymentCatalogEntry(BaseModel):
    IdFormaPago: int | None
    FormaPago: str | None
    Codigo: str | int | None
    Activa: int | None
    EnviaDatafono: int | None


class HoseArticleFilters(StrictModel):
    nIdArt: int | None = Field(default=None, ge=-2147483648, le=2147483647)
    nIsla: str | None = Field(default=None, max_length=40)


class HoseByArticle(BaseModel):
    IdManguera: int | None
    CodigoManguera: int | str | None
    IdCara: int | None
    IdIsla: int | None
    CodigoIsla: int | str | None
    CodigoArticulo: str | int | None
    Descripcion: str | None
