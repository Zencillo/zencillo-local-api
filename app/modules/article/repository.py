from enum import Enum
from functools import cache
from importlib.resources import files

from app.core.database import SqlDatabase
from app.modules.article.schemas import (
    EcuadorSubsidy, ExpenseType, Face, FaceWithHose, Fuel, FuelByFace, Hose, HoseByArticle,
    PaymentCatalogEntry, RoundingConfig, VehicleType,
)


class ArticleQuery(Enum):
    PANTERA_ARTICLES = "pantera_articles.sql"
    DELETE_SUBSIDIES = "delete_subsidies.sql"
    UPDATE_SUBSIDY = "update_subsidy.sql"
    INSERT_SUBSIDY = "insert_subsidy.sql"
    STATION_ARTICLES = "station_articles.sql"
    DELETE_VEHICLE_TYPES = "delete_vehicle_types.sql"
    INSERT_VEHICLE_TYPE = "insert_vehicle_type.sql"
    DELETE_EXPENSE_TYPES = "delete_expense_types.sql"
    INSERT_EXPENSE_TYPE = "insert_expense_type.sql"
    VEHICLE_TYPES = "vehicle_types.sql"
    EXPENSE_TYPES = "expense_types.sql"
    ROUNDING_CONFIG = "rounding_config.sql"
    FUELS = "fuels.sql"
    FUELS_BY_FACE = "fuels_by_face.sql"
    HOSES = "hoses.sql"
    HOSES_BY_ARTICLE = "hoses_by_article.sql"
    FACES = "faces.sql"
    FACES_WITH_HOSES = "faces_with_hoses.sql"
    ECUADOR_SUBSIDIES = "subsidies_ecuador.sql"
    SUBSIDY_FACTOR = "subsidy_factor.sql"
    PAYMENT_CATALOG = "payment_catalog.sql"
    CHANGE_PAYMENT_CATALOG = "change_payment_catalog.sql"


@cache
def load_query(query: ArticleQuery) -> str:
    if not isinstance(query, ArticleQuery):
        raise TypeError("Se requiere una consulta registrada del modulo de articulos.")
    return files(__package__).joinpath("queries", query.value).read_text(encoding="utf8").strip()


class ArticleRepository:
    def __init__(self, db: SqlDatabase):
        self.db = db

    def list_vehicle_types(self) -> list[VehicleType]:
        return self.db.read(load_query(ArticleQuery.VEHICLE_TYPES), VehicleType)

    def list_expense_types(self) -> list[ExpenseType]:
        return self.db.read(load_query(ArticleQuery.EXPENSE_TYPES), ExpenseType)

    def list_rounding_config(self) -> list[RoundingConfig]:
        return self.db.read(load_query(ArticleQuery.ROUNDING_CONFIG), RoundingConfig)

    def list_fuels(self) -> list[Fuel]:
        return self.db.read(load_query(ArticleQuery.FUELS), Fuel)

    def list_fuels_by_face(self) -> list[FuelByFace]:
        return self.db.read(load_query(ArticleQuery.FUELS_BY_FACE), FuelByFace)


    def list_hoses(self) -> list[Hose]:
        return self.db.read(load_query(ArticleQuery.HOSES), Hose)

    def list_faces(self, *, gnIsla: int, gnNumeroCapturador: int, isMultiIsla: bool) -> list[Face]:
        return self.db.read(
            load_query(ArticleQuery.FACES), Face,
            parameters=(int(isMultiIsla), gnIsla, gnNumeroCapturador, gnNumeroCapturador),
        )

    def list_faces_with_hoses(self, *, codigoIsla: str) -> list[FaceWithHose]:
        return self.db.read(load_query(ArticleQuery.FACES_WITH_HOSES), FaceWithHose, parameters=(codigoIsla,))


    def list_ecuador_subsidies(self) -> list[EcuadorSubsidy]:
        return self.db.read(load_query(ArticleQuery.ECUADOR_SUBSIDIES), EcuadorSubsidy)

    def list_payment_catalog(self) -> list[PaymentCatalogEntry]:
        return self.db.read(load_query(ArticleQuery.PAYMENT_CATALOG), PaymentCatalogEntry)

    def list_change_payment_catalog(self) -> list[PaymentCatalogEntry]:
        return self.db.read(load_query(ArticleQuery.CHANGE_PAYMENT_CATALOG), PaymentCatalogEntry)


    def list_hoses_by_article(self, *, nIdArt: int | None, nIsla: str | None) -> list[HoseByArticle]:
        parameters = (1, nIdArt, nIsla) if nIdArt is not None and nIsla is not None else (0, None, None)
        return self.db.read(load_query(ArticleQuery.HOSES_BY_ARTICLE), HoseByArticle, parameters=parameters)
