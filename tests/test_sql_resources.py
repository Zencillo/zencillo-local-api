from unittest.mock import MagicMock

import pytest

from app.config import Settings
from app.core.database import SqlDatabase
from app.modules.article.repository import ArticleQuery, load_query
from app.modules.article.schemas import VehicleType
from tools.run_phase6_demo import REFERENCES


def test_embedded_queries_equal_independent_legacy_references():
    expected = {
        ArticleQuery.VEHICLE_TYPES: "ListarTiposVehiculo",
        ArticleQuery.EXPENSE_TYPES: "ListarTiposGasto",
        ArticleQuery.ROUNDING_CONFIG: "ListarConfiguracionRedondeo",
        ArticleQuery.FUELS: "ListarCombustibles",
    }
    assert set(expected) <= set(ArticleQuery)
    for query, operation in expected.items():
        assert load_query(query) == REFERENCES[operation][0]


@pytest.mark.parametrize("value", ["vehicle_types.sql", "../../.env", "SELECT 1"])
def test_loader_refuses_raw_names_paths_and_sql(value):
    with pytest.raises(TypeError):
        load_query(value)


def test_database_binds_parameters_separately():
    settings = MagicMock(spec=Settings)
    settings.connection_string = "test-only"
    settings.sql_timeout = 5
    connect = MagicMock()
    cursor = connect.return_value.cursor.return_value
    cursor.description = [("idtipovehiculo",), ("tipovehiculo",)]
    cursor.fetchall.return_value = []
    statement = "SELECT idtipovehiculo, tipovehiculo FROM tipo_vehiculo WHERE tipovehiculo = ?"
    parameter = "O'Reilly; --"
    assert SqlDatabase(settings, connect).read(
        statement, VehicleType, parameters=(parameter,),
    ) == []
    cursor.execute.assert_called_once_with(statement, parameter)
