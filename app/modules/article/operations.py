from pydantic import BaseModel, Field, FiniteFloat

from app.schemas import SqlScalar, StrictModel, WriteResult

from app.core.registry import Operation, request_actor
from app.errors import ApiError
from app.modules.article.repository import ArticleQuery, ArticleRepository, load_query
from app.modules.article.schemas import EcuadorSubsidy, FaceFilters, HoseArticleFilters, IslandCode
from app.schemas import NoParameters


class ArticleFilters(StrictModel):
    isCombustible: bool
    idPuntoVenta: int | None = Field(ge=-2147483648, le=2147483647)


class StationArticle(BaseModel):
    IdArticulo: SqlScalar
    IdTarifaIVA: SqlScalar
    IdPresentacion: SqlScalar
    CodigoArticulo: SqlScalar
    CodigoAlterno: SqlScalar
    PrecioAbierto: SqlScalar
    IncluyeIVA: SqlScalar
    Articulo: SqlScalar
    NombreCorto: SqlScalar
    Precio: SqlScalar
    Presentacion: SqlScalar
    PresentacionUnidades: SqlScalar
    Porcentaje: SqlScalar
    CodigoICE: SqlScalar
    PorcentajeICE: SqlScalar
    Combustible: SqlScalar
    Estado: SqlScalar
    ImpuestoValorFijo: SqlScalar
    ExisteRegistro: SqlScalar
    Existencia: SqlScalar


class SubsidyFactorFilter(StrictModel):
    idArticulo: str = Field(max_length=100)
    ano: int = Field(ge=-2147483648, le=2147483647)
    mes: int = Field(ge=-2147483648, le=2147483647)


class SubsidyEntry(StrictModel):
    idArticulo: int = Field(ge=-2147483648, le=2147483647)
    subsidioFactor: FiniteFloat
    ano: int = Field(ge=-2147483648, le=2147483647)
    mes: int = Field(ge=-2147483648, le=2147483647)


class SubsidyReplace(StrictModel):
    items: list[SubsidyEntry] = Field(min_length=1, max_length=5000)


class VehicleTypeEntry(StrictModel):
    idtipovehiculo: int = Field(ge=-2147483648, le=2147483647)
    tipovehiculo: str = Field(max_length=50)


class ExpenseTypeEntry(StrictModel):
    idgastotipo: int = Field(ge=-2147483648, le=2147483647)
    idcompania: int = Field(ge=-2147483648, le=2147483647)
    gastotipo: str = Field(max_length=50)
    contabilidadcuenta: str = Field(max_length=50)
    estado: int = Field(ge=0, le=1)
    fechacreacion: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
    fechamodificacion: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
    fechaultimomovimiento: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


class VehicleTypeReplace(StrictModel):
    items: list[VehicleTypeEntry] = Field(min_length=1, max_length=5000)


class ExpenseTypeReplace(StrictModel):
    items: list[ExpenseTypeEntry] = Field(min_length=1, max_length=5000)


class PanteraArticle(BaseModel):
    IdArticulo: SqlScalar
    IdTarifaIVA: SqlScalar
    IdPresentacion: SqlScalar
    CodigoArticulo: SqlScalar
    CodigoAlterno: SqlScalar
    PrecioAbierto: SqlScalar
    IncluyeIVA: SqlScalar
    Articulo: SqlScalar
    NombreCorto: SqlScalar
    Precio: SqlScalar
    Presentacion: SqlScalar
    PresentacionUnidades: SqlScalar
    Porcentaje: SqlScalar
    CodigoICE: SqlScalar
    PorcentajeICE: SqlScalar
    Combustible: SqlScalar
    Estado: SqlScalar
    ImpuestoValorFijo: SqlScalar



def article_operations(repository: ArticleRepository) -> dict[str, Operation]:
    def station_articles(*, isCombustible: bool, idPuntoVenta: int | None):
        return repository.db.read(
            load_query(ArticleQuery.STATION_ARTICLES), StationArticle,
            parameters=(0 if idPuntoVenta is None else idPuntoVenta, int(isCombustible)),
        )

    def pantera_articles():
        return repository.db.read(load_query(ArticleQuery.PANTERA_ARTICLES), PanteraArticle)

    def subsidy_factor(*, idArticulo: str, ano: int, mes: int):
        return repository.db.read(load_query(ArticleQuery.SUBSIDY_FACTOR), EcuadorSubsidy,
                                  parameters=(idArticulo, ano, mes))

    return {
        "ConsultarSubsidioEcuadorArticulo": (SubsidyFactorFilter, subsidy_factor),
        "ListarArticulosPanteraPago": (NoParameters, pantera_articles),
        "ListarArticulosEstacion": (ArticleFilters, station_articles),
        "ListarTiposVehiculo": (NoParameters, repository.list_vehicle_types),
        "ListarTiposGasto": (NoParameters, repository.list_expense_types),
        "ListarConfiguracionRedondeo": (NoParameters, repository.list_rounding_config),
        "ListarCombustibles": (NoParameters, repository.list_fuels),
        "ListarCombustiblesPorCara": (NoParameters, repository.list_fuels_by_face),
        "ListarManguerasTanques": (NoParameters, repository.list_hoses),
        "ListarManguerasPorArticuloEIsla": (HoseArticleFilters, repository.list_hoses_by_article),
        "ListarCarasFiltradas": (FaceFilters, repository.list_faces),
        "ListarCarasSurtidores": (IslandCode, repository.list_faces_with_hoses),
        "ListarSubsidiosEcuador": (NoParameters, repository.list_ecuador_subsidies),
        "ListarFormasPagoPOS": (NoParameters, repository.list_payment_catalog),
        "ListarCambiosFormaPagoPOS": (NoParameters, repository.list_change_payment_catalog),
    }


def article_write_operations(repository: ArticleRepository) -> dict[str, Operation]:
    def replace_subsidies(*, items):
        delete = load_query(ArticleQuery.DELETE_SUBSIDIES)
        insert = load_query(ArticleQuery.INSERT_SUBSIDY)
        repository.db.write([
            (delete, ()),
            *((insert, (item["idArticulo"], item["subsidioFactor"], item["ano"], item["mes"]))
              for item in items),
        ])
        return [WriteResult()]

    def replace_vehicle_types(*, items):
        delete = load_query(ArticleQuery.DELETE_VEHICLE_TYPES)
        insert = load_query(ArticleQuery.INSERT_VEHICLE_TYPE)
        repository.db.write([
            (delete, ()),
            *((insert, (item["idtipovehiculo"], item["tipovehiculo"])) for item in items),
        ])
        return [WriteResult()]

    def replace_expense_types(*, items):
        delete = load_query(ArticleQuery.DELETE_EXPENSE_TYPES)
        insert = load_query(ArticleQuery.INSERT_EXPENSE_TYPE)
        repository.db.write([
            (delete, ()),
            *((insert, (item["idgastotipo"], item["idcompania"], item["gastotipo"],
                        item["contabilidadcuenta"], item["estado"], item["fechacreacion"],
                        item["fechamodificacion"], item["fechaultimomovimiento"])) for item in items),
        ])
        return [WriteResult()]

    return {
        "ReemplazarSubsidiosEcuador": (SubsidyReplace, replace_subsidies),
        "ReemplazarTiposVehiculo": (VehicleTypeReplace, replace_vehicle_types),
        "ReemplazarTiposGasto": (ExpenseTypeReplace, replace_expense_types),
    }


class SqlAffectedRows(BaseModel):
    affectedRows: int


def article_statement_operations(repository: ArticleRepository, guard: str) -> dict[str, Operation]:
    def statement(query, params=()):
        station, _ = request_actor.get()
        if station != '900716/10370/1':
            raise ApiError(403, 'STATION_MISMATCH', 'Estación no autorizada para el piloto')
        count = repository.db.write([(guard, ()), (load_query(query), params)], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def delete():
        return statement(ArticleQuery.DELETE_SUBSIDIES)

    def insert(*, idArticulo, subsidioFactor, ano, mes):
        return statement(ArticleQuery.INSERT_SUBSIDY, (idArticulo, subsidioFactor, ano, mes))

    def update(*, idArticulo, subsidioFactor, ano, mes):
        return statement(ArticleQuery.UPDATE_SUBSIDY, (subsidioFactor, ano, mes, idArticulo))

    def delete_vehicles():
        return statement(ArticleQuery.DELETE_VEHICLE_TYPES)

    def delete_expenses():
        return statement(ArticleQuery.DELETE_EXPENSE_TYPES)

    def insert_vehicle(*, idtipovehiculo, tipovehiculo):
        return statement(ArticleQuery.INSERT_VEHICLE_TYPE, (idtipovehiculo, tipovehiculo))

    def insert_expense(*, idgastotipo, idcompania, gastotipo, contabilidadcuenta, estado,
                       fechacreacion, fechamodificacion, fechaultimomovimiento):
        if idcompania != 900716:
            raise ApiError(403, 'STATION_MISMATCH', 'Compañía no autorizada')
        return statement(ArticleQuery.INSERT_EXPENSE_TYPE, (idgastotipo, idcompania, gastotipo,
            contabilidadcuenta, estado, fechacreacion, fechamodificacion, fechaultimomovimiento))

    return {'EliminarTiposVehiculo': (NoParameters, delete_vehicles),
            'EliminarTiposGasto': (NoParameters, delete_expenses),
            'InsertarTipoVehiculo': (VehicleTypeEntry, insert_vehicle),
            'InsertarTipoGasto': (ExpenseTypeEntry, insert_expense),
            'EliminarSubsidiosEcuador': (NoParameters, delete),
            'InsertarSubsidioEcuador': (SubsidyEntry, insert),
            'ActualizarSubsidioEcuador': (SubsidyEntry, update)}
