from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import jwt
import pyodbc
import pytest
from fastapi.testclient import TestClient

from app.config import Device, Settings
from app.main import create_app
from app.core.security import hash_secret, matches

QUERY = {"Query": "ListarTiposVehiculo", "parameters": {}}


@pytest.fixture
def setup():
    digest = hash_secret("test-device-secret")
    settings = Settings(
        jwt_key="test-only-key-not-for-deployment-123",
        station="station-test",
        connection_string="mock-connection",
        devices={
            "allowed": Device(station="station-test", secret_hash=digest,
                              operations={"ListarTiposVehiculo"}),
            "denied": Device(station="station-test", secret_hash=digest, operations=set()),
        },
    )
    connect = MagicMock()
    cursor = connect.return_value.cursor.return_value
    cursor.description = [("idtipovehiculo",), ("tipovehiculo",)]
    with TestClient(create_app(settings, connect=connect)) as client:
        yield client, connect, cursor, settings


def login(client, device="allowed", secret="test-device-secret"):
    return client.post("/v1/auth/token", json={"device_id": device, "secret": secret})


def headers(client, device="allowed"):
    token = login(client, device).json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def check_error(response, status, code):
    assert response.status_code == status
    body = response.json()
    assert set(body) == {"success", "message", "data", "error"}
    assert body["success"] is False and body["data"] is None
    assert body["message"]
    assert body["error"] == {"code": code}


def test_hash():
    encoded = hash_secret("value")
    assert matches("value", encoded)
    assert not matches("wrong", encoded)
    assert not matches("value", "invalid")


def test_login(setup):
    client, _, _, settings = setup
    response = login(client)
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    claims = jwt.decode(token, settings.jwt_key, algorithms=["HS256"],
                        audience=settings.audience, issuer=settings.issuer)
    assert (claims["station"], claims["sub"]) == ("station-test", "allowed")


def test_wrong_secret(setup):
    check_error(login(setup[0], secret="wrong"), 401, "UNAUTHENTICATED")


def test_license_bootstrap_precedes_license_authenticated_token():
    settings = Settings(
        jwt_key="test-only-key-not-for-deployment-123",
        station="900716/1/1",
        connection_string="mock-connection",
        devices={
            "allowed": Device(
                station="900716/1/1",
                secret_hash=hash_secret("test-device-secret"),
                operations={"ObtenerLicenciaCloudCapturador"},
            ),
        },
    )
    connect = MagicMock()
    cursor = connect.return_value.cursor.return_value
    cursor.description = [("UsuarioLicencia",), ("ContrasenaLicencia",)]
    cursor.fetchall.return_value = [("license-user", "license-password")]
    with TestClient(create_app(settings, connect=connect)) as client:
        bootstrap = client.post(
            "/v1/auth/license",
            json={},
        )
        assert bootstrap.status_code == 200
        assert bootstrap.json()["data"] == {
            "idCompany": 900716,
            "user": "license-user",
            "password": "license-password",
        }

        token = client.post(
            "/v1/auth/token",
            json={
                "device_id": "allowed",
                "secret": "test-device-secret",
                "licenseCompany": "900716",
                "licenseUser": "license-user",
                "licensePassword": "license-password",
            },
        )
        assert token.status_code == 200

        cursor.description = [
            ("IdCompania",), ("IdCentroVenta",), ("CodigoIsla",),
            ("UsuarioLicencia",), ("ContrasenaLicencia",),
        ]
        cursor.fetchall.return_value = [
            (900716, 1, 1, "license-user", "license-password"),
        ]
        token_without_device_secret = client.post(
            "/v1/auth/token",
            json={
                "device_id": "allowed",
                "licenseCompany": "900716",
                "licenseUser": "license-user",
                "licensePassword": "license-password",
            },
        )
        assert token_without_device_secret.status_code == 200

        rejected = client.post(
            "/v1/auth/token",
            json={
                "device_id": "allowed",
                "licenseCompany": "900716",
                "licenseUser": "license-user",
                "licensePassword": "wrong",
            },
        )
        check_error(rejected, 401, "LICENSE_LOGIN_REJECTED")


@pytest.mark.parametrize("authorization", [None, "Bearer invalid"])
def test_invalid_token(setup, authorization):
    client, connect, _, _ = setup
    result = client.post("/v1/operations", json=QUERY,
                         headers={"Authorization": authorization} if authorization else {})
    check_error(result, 401, "UNAUTHENTICATED")
    connect.assert_not_called()


def test_station_mismatch(setup):
    client, connect, _, settings = setup
    raw = headers(client)["Authorization"][7:]
    claims = jwt.decode(raw, options={"verify_signature": False})
    claims["station"] = "other"
    token = jwt.encode(claims, settings.jwt_key, algorithm="HS256")
    result = client.post("/v1/operations", json=QUERY,
                         headers={"Authorization": f"Bearer {token}"})
    check_error(result, 403, "STATION_MISMATCH")
    connect.assert_not_called()


@pytest.mark.parametrize("device,request_body,status,code", [
    ("denied", QUERY, 403, "FORBIDDEN"),
    ("allowed", {"Query": "Unknown", "parameters": {}}, 404, "OPERATION_NOT_FOUND"),
    ("allowed", {"Query": "SELECT 1", "parameters": {}}, 404, "OPERATION_NOT_FOUND"),
    ("allowed", {"Query": "ListarTiposVehiculo", "parameters": {"extra": True}},
     400, "INVALID_PARAMETERS"),
    ("allowed", {"Query": "ListarTiposVehiculo", "parameters": []}, 400, "INVALID_REQUEST"),
])
def test_request_rejected_without_sql(setup, device, request_body, status, code):
    client, connect, _, _ = setup
    result = client.post("/v1/operations", json=request_body, headers=headers(client, device))
    check_error(result, status, code)
    connect.assert_not_called()


@pytest.mark.parametrize("rows,items", [
    ([(Decimal("9"), " Camión "), (None, None)],
     [{"idtipovehiculo": 9, "tipovehiculo": " Camión "},
      {"idtipovehiculo": None, "tipovehiculo": None}]),
    ([], []),
])
def test_read_and_serialization(setup, rows, items):
    client, connect, cursor, settings = setup
    cursor.fetchall.return_value = rows
    result = client.post("/v1/operations", json=QUERY, headers=headers(client))
    assert result.status_code == 200
    assert result.json() == {
        "success": True, "message": "Operación completada", "data": {"items": items},
    }
    cursor.execute.assert_called_once_with("SELECT idtipovehiculo, tipovehiculo FROM tipo_vehiculo")
    cursor.close.assert_called_once()
    connect.return_value.close.assert_called_once()
    assert connect.return_value.timeout == settings.sql_timeout


@pytest.mark.parametrize("state,status,code", [
    ("08001", 503, "SQL_UNAVAILABLE"), ("HYT00", 504, "SQL_TIMEOUT"),
])
def test_sql_error_is_controlled(setup, state, status, code):
    client, connect, cursor, _ = setup
    cursor.execute.side_effect = pyodbc.Error(state, "SECRET driver error")
    result = client.post("/v1/operations", json=QUERY, headers=headers(client))
    check_error(result, status, code)
    assert "SECRET" not in result.text
    cursor.close.assert_called_once()
    connect.return_value.close.assert_called_once()


@pytest.mark.parametrize("operation,sql,columns,row,expected", [
    ("ListarTiposGasto", "SELECT * FROM gasto_tipo WHERE estado = 1",
     ("idcompania", "idgastotipo", "gastotipo", "contabilidadcuenta", "estado",
      "fechacreacion", "fechamodificacion", "fechaultimomovimiento", "campoInterno"),
     (1, 2, "Peaje", "0001", True, datetime(2026, 11, 24), None, None, "privado"),
     {"idcompania": 1, "idgastotipo": 2, "gastotipo": "Peaje", "contabilidadcuenta": "0001",
      "estado": True, "fechacreacion": "2026-11-24T00:00:00", "fechamodificacion": None,
      "fechaultimomovimiento": None, "campoInterno": "privado"}),
    ("ListarConfiguracionRedondeo",
     "SELECT [Documento], [Posicion], [Descripcion], [AplicaRedondeo], [FactorRedondeo] FROM [ConfiguracionRedondeo]",
     ("Documento", "Posicion", "Descripcion", "AplicaRedondeo", "FactorRedondeo"),
     ("FC", 2, None, False, Decimal("0.05")),
     {"Documento": "FC", "Posicion": 2, "Descripcion": None, "AplicaRedondeo": 0, "FactorRedondeo": 0.05}),
    ("ListarConfiguracionRedondeo",
     "SELECT [Documento], [Posicion], [Descripcion], [AplicaRedondeo], [FactorRedondeo] FROM [ConfiguracionRedondeo]",
     ("Documento", "Posicion", "Descripcion", "AplicaRedondeo", "FactorRedondeo"),
     (4, 2, "Demo", True, 5),
     {"Documento": 4, "Posicion": 2, "Descripcion": "Demo", "AplicaRedondeo": 1, "FactorRedondeo": 5}),
    ("ListarCombustibles",
     "SELECT [IdCombustible], [IdArticulo], [Color], [Nombre], [CodigoArticulo] FROM [Combustible]",
     ("IDCOMBUSTIBLE", "IdArticulo", "Color", "Nombre", "CodigoArticulo"),
     (3, 4, None, "DiÃ©sel", "0121"),
     {"IDCOMBUSTIBLE": 3, "IdArticulo": 4, "Color": None, "Nombre": "DiÃ©sel", "CodigoArticulo": "0121"}),
])
def test_phase6_catalogs(setup, operation, sql, columns, row, expected):
    client, connect, cursor, settings = setup
    cursor.description = [(column,) for column in columns]
    cursor.fetchall.return_value = [row]
    request = {"Query": operation, "parameters": {}}
    unauthorized = client.post("/v1/operations", json=request, headers=headers(client))
    check_error(unauthorized, 403, "FORBIDDEN")
    settings.devices["allowed"] = settings.devices["allowed"].model_copy(
        update={"operations": frozenset({operation})},
    )
    auth = headers(client)
    extra = {**request, "parameters": {"sql": "SELECT 1"}}
    check_error(client.post("/v1/operations", json=extra, headers=auth), 400, "INVALID_PARAMETERS")
    connect.assert_not_called()
    response = client.post("/v1/operations", json=request, headers=auth)
    assert response.status_code == 200
    assert response.json()["data"]["items"] == [expected]
    cursor.execute.assert_called_once_with(sql)
    cursor.fetchall.return_value = []
    assert client.post("/v1/operations", json=request, headers=auth).json()["data"]["items"] == []



def test_odbc_diagnostic_correlates_request_and_logs_only_controlled_fields(setup, caplog):
    client, connect, _, _ = setup
    connect.side_effect = pyodbc.Error(
        "08001", "[SSL Provider] (10054) fixture-text-that-must-not-be-logged",
    )
    result = client.post("/v1/operations", json=QUERY, headers=headers(client))
    check_error(result, 503, "SQL_UNAVAILABLE")
    request_id = result.headers["X-Request-ID"]
    assert len(request_id) == 32
    assert f"request_id={request_id} operation=ListarTiposVehiculo" in caplog.text
    assert "connect_ms=" in caplog.text
    assert "active_at_start=1 active=1 category=socket_reset native=10054" in caplog.text
    assert "fixture-text-that-must-not-be-logged" not in caplog.text


def test_odbc_distinguishes_certificate_trust_from_generic_08001():
    from app.core.database import odbc_failure

    assert odbc_failure(pyodbc.Error("08001", "SSL Provider (-2146893019)")) == (
        "08001", "certificate_trust", "-2146893019",
    )
    assert odbc_failure(pyodbc.Error("08001", "client unable to establish connection (123456789)")) == (
        "08001", "unclassified", "-",
    )


def test_phase13_faces_binds_text_parameters(setup):
    from app.modules.article.schemas import FaceWithHose

    client, connect, cursor, settings = setup
    operation = "ListarCarasSurtidores"
    settings.devices["allowed"] = settings.devices["allowed"].model_copy(
        update={"operations": frozenset({operation})},
    )
    auth = headers(client)
    check_error(client.post(
        "/v1/operations", json={"Query": operation, "parameters": {"codigoIsla": 1}},
        headers=auth,
    ), 400, "INVALID_PARAMETERS")
    connect.assert_not_called()

    expected = dict.fromkeys(FaceWithHose.model_fields)
    expected.update(CodigoIsla="001", CodigoArticulo="0121")
    cursor.description = [(column,) for column in expected]
    cursor.fetchall.return_value = [tuple(expected.values())]
    response = client.post(
        "/v1/operations", json={"Query": operation, "parameters": {"codigoIsla": "001"}},
        headers=auth,
    )
    assert response.status_code == 200
    assert response.json()["data"]["items"] == [expected]
    sql, code = cursor.execute.call_args.args
    assert "?" in sql and "001" not in sql
    assert code == "001"


def test_phase13_fuel_by_face_preserves_null_and_legacy_bit(setup):
    from app.modules.article.schemas import FuelByFace

    client, _, cursor, settings = setup
    operation = "ListarCombustiblesPorCara"
    settings.devices["allowed"] = settings.devices["allowed"].model_copy(
        update={"operations": frozenset({operation})},
    )
    values = dict.fromkeys(FuelByFace.model_fields)
    values.update(CodigoArticulo="0121", PrecioAbierto=True, PrecioArticulo=Decimal("3.14"))
    cursor.description = [(column,) for column in values]
    cursor.fetchall.return_value = [tuple(values.values())]
    response = client.post(
        "/v1/operations", json={"Query": operation, "parameters": {}},
        headers=headers(client),
    )
    assert response.status_code == 200
    item, = response.json()["data"]["items"]
    assert set(item) == set(values)
    assert item["CodigoArticulo"] == "0121"
    assert item["IdPresentacion"] is None
    assert type(item["PrecioAbierto"]) is bool and item["PrecioAbierto"] is True
    assert item["PrecioArticulo"] == 3.14


@pytest.mark.parametrize("name,params,schema,forbidden", [
    ("ListarConfiguracionOperativaPOS", {}, "PosStartup", "ContrasenaPinPad"),
    ("ConsultarEstadoTurnoYZeta", {"isla": 1}, "ShiftStartup", "ContrasenaEmpleadoTurno"),
    ("ListarConfiguracionOperativaGeneral", {}, "GeneralStartup", "ContrasenaLicencia"),
])
def test_phase14_projects_operational_columns(setup, name, params, schema, forbidden):
    from app.modules.license import operations

    client, _, cursor, settings = setup
    settings.devices["allowed"] = settings.devices["allowed"].model_copy(
        update={"operations": frozenset({name})},
    )
    values = dict.fromkeys(getattr(operations, schema).model_fields)
    values[forbidden] = "fixture-sensitive"
    cursor.description = [(column,) for column in values]
    cursor.fetchall.return_value = [tuple(values.values())]
    response = client.post(
        "/v1/operations", json={"Query": name, "parameters": params},
        headers=headers(client),
    )
    assert response.status_code == 200
    assert "fixture-sensitive" not in response.text
    expected = {key: value for key, value in values.items() if key != forbidden}
    assert response.json()["data"]["items"] == [expected]
    sql, *bound = cursor.execute.call_args.args
    assert forbidden not in sql
    assert bound == list(params.values())


def test_phase14_capturer_config_cannot_request_arbitrary_keys(setup):
    client, connect, cursor, settings = setup
    name = "ListarConfiguracionOperativaCapturador"
    settings.devices["allowed"] = settings.devices["allowed"].model_copy(
        update={"operations": frozenset({name})},
    )
    auth = headers(client)
    response = client.post(
        "/v1/operations",
        json={"Query": name, "parameters": {"Llave": "fixture-sensitive"}},
        headers=auth,
    )
    check_error(response, 400, "INVALID_PARAMETERS")
    connect.assert_not_called()
    cursor.description = [("Valor",), ("Llave",)]
    cursor.fetchall.return_value = [("001", "TIMEOUT_IMPRESION")]
    response = client.post(
        "/v1/operations", json={"Query": name, "parameters": {}}, headers=auth,
    )
    assert response.status_code == 200
    assert response.json()["data"]["items"] == [{"Llave": "TIMEOUT_IMPRESION", "Valor": "001"}]
    sql, = cursor.execute.call_args.args
    assert sql.strip() == "SELECT Valor, Llave\nFROM ConfiguracionCapturador"
    assert "CLIENT_SECRET" not in sql



@pytest.mark.parametrize("name,params,columns,row", [
    ("ConsultarContratoCreditoLocal", {"key": "0001"},
     ["idcontratocredito", "idcliente", "identificacion", "cliente", "fechainicio", "fechafin",
      "descripcion", "numero"], (1, 17, "0001", "CLIENTE FICTICIO", None, None, None, "0009")),
    ("ConsultarSubsidioEcuadorArticulo", {"idArticulo": "0001", "ano": 2026, "mes": 11},
     ["IdArticulo", "SubsidioFactor", "Ano", "Mes"], (1, 0.125, 2026, 11)),
    ("ListarDiferenciasPrecioEspecialTurno", {"idTurno": 17},
     ["IdManguera", "Surtidor", "Cara", "Manguera", "SubtotalReferencia", "SubtotalReal"],
     (12, "01", "02", "03", 47040.0, 50000.0)),
    ("ConsultarExisteTurnoAbiertoIsla", {"isla": 1}, ["Abierto"], (1,)),
    ("ListarHistorialPresetsTurno", {"idTurno": 17},
     ["IdHistorialPreset", "Cantidad", "Hora", "Cara", "Tipo", "IdTurno", "Producto"],
     (1, 2.5, "003600", 1, 0, 17, "CORRIENTE")),
    ("ConsultarAsignacionCapturador", {"idIsla": 2, "numeroCapturador": 3},
     ["IdCapturadorCaras", "IdIsla", "NumeroCapturador", "Puerto", "IP"], (17, 2, 3, 8765, None)),
    ("ListarExistenciasPuntoVenta", {"idPuntoVenta": -1},
     ["CodigoArticulo", "Articulo", "NombreCorto", "saldo"], ("001", "Demo", None, 2)),
    ("ListarGastosAcumuladosTurno", {"idTurno": 8},
     ["gasto", "total"], ("Peaje", 2.5)),
    ("ListarBolsasAcumuladasTurno", {"idTurno": 8},
     ["IdTurno", "CodigoBolsa", "ValorBillete", "ValorMoneda", "Nota"], (8, "001", 2.5, None, None)),
])
def test_station_queries_bind_existing_filters_and_preserve_values(setup, name, params, columns, row):
    client, connect, cursor, settings = setup
    settings.devices["allowed"] = settings.devices["allowed"].model_copy(
        update={"operations": frozenset({name})},
    )
    auth = headers(client)
    error = client.post("/v1/operations", headers=auth,
                        json={"Query": name, "parameters": {**params, "sql": "SELECT 1"}})
    check_error(error, 400, "INVALID_PARAMETERS")
    connect.assert_not_called()
    cursor.description = [(column,) for column in columns]
    cursor.fetchall.return_value = [row]
    response = client.post("/v1/operations", headers=auth, json={"Query": name, "parameters": params})
    assert response.status_code == 200
    item, = response.json()["data"]["items"]
    assert item == dict(zip(columns, row))
    assert [type(item[key]) for key in columns] == [type(value) for value in row]
    sql, *bound = cursor.execute.call_args.args
    assert sql.count("?") == len(params)
    assert bound == list(params.values())



@pytest.mark.parametrize("operation,parameters,statement,bindings", [
    ("GuardarPlacaOffline", {"placa":"ZS123", "identificadorPlaca":"TAG", "identificacion":"LAB", "correoPlaca":""},
     "EXEC dbo.sp_UpsertClientePlacaOffLine", ("ZS123", "TAG", "LAB", "")),
    ("GuardarClienteOffline", {"identificacion": "LAB-TEST", "nombreCliente": "Demo"},
     "EXEC dbo.sp_UpsertClienteOffLine", ("LAB-TEST", "Demo", None, None, None, None, None, None, None)),
    ("ReemplazarSubsidiosEcuador", {"items": [{"idArticulo": 10, "subsidioFactor": 0.125, "ano": 2090, "mes": 11}]},
     "INSERT INTO SubsidioEcuador", (10, 0.125, 2090, 11)),
])
@pytest.mark.parametrize("fail", [False, True])
def test_station_writes_commit_or_roll_back_a_single_transaction(setup, operation, parameters, statement, bindings, fail):
    _, connect, cursor, settings = setup
    settings.devices["allowed"] = settings.devices["allowed"].model_copy(
        update={"operations": frozenset({operation})},
    )
    cursor.nextset.return_value = False
    cursor.fetchone.return_value = (1, 1)
    application = create_app(settings, connect=connect)

    def execute(sql, *params):
        if statement in sql:
            assert params == bindings
            if fail:
                raise pyodbc.Error("22003", "fixture error")

    cursor.execute.side_effect = execute
    with TestClient(application) as client:
        response = client.post("/v1/operations", headers=headers(client), json={
            "Query": operation, "parameters": parameters,
        })
    assert connect.call_count == 1 and connect.call_args.kwargs["autocommit"] is False
    if fail:
        check_error(response, 503, "SQL_WRITE_FAILED")
        connect.return_value.rollback.assert_called_once()
        connect.return_value.commit.assert_not_called()
    else:
        assert response.status_code == 200
        assert response.json()["data"]["items"] == [{"applied": True}]
        connect.return_value.commit.assert_called_once()
        connect.return_value.rollback.assert_not_called()


@pytest.mark.parametrize("operation", ["GuardarClienteOffline", "ReemplazarSubsidiosEcuador", "GuardarPlacaOffline", "GuardarConfiguracionEcuador"])
def test_station_writes_require_an_explicit_device_permission(setup, operation):
    client, connect, _, _ = setup
    response = client.post("/v1/operations", headers=headers(client), json={
        "Query": operation, "parameters": {},
    })
    check_error(response, 403, "FORBIDDEN")
    connect.assert_not_called()

@pytest.mark.parametrize("fails", [False, True])
def test_ecuador_save_is_one_transaction_with_fixed_keys(setup, fails):
    _, connect, cursor, settings = setup
    operation = "GuardarConfiguracionEcuador"
    settings.devices["allowed"] = settings.devices["allowed"].model_copy(
        update={"operations": frozenset({operation})},
    )
    cursor.nextset.return_value = False
    cursor.fetchone.return_value = (1, 1)
    names = []

    def execute(sql, *parameters):
        if "UPDATE dbo.ConfiguracionCapturador" in sql:
            names.append(parameters)
            if fails and len(names) == 2:
                raise pyodbc.Error("22003", "fixture")

    cursor.execute.side_effect = execute
    with TestClient(create_app(settings, connect=connect)) as client:
        token = headers(client)
        denied = client.post("/v1/operations", headers=token, json={
            "Query": operation, "parameters": {"llave": "NO_PERMITIDA", "valor": "X"},
        })
        check_error(denied, 400, "INVALID_PARAMETERS")
        connect.assert_not_called()
        response = client.post("/v1/operations", headers=token, json={
            "Query": operation, "parameters": {
                "placaEnvases": "Z'S", "prefijoCuantias": "LAB", "prefijoMaquinarias": "",
            },
        })
    expected = [
        ("ECUADOR_PLACA_ENVASES", "Z'S"), ("ECUADOR_PREFIJO_CUANTIAS", "LAB"),
        ("ECUADOR_PREFIJO_MAQUINARIAS", ""),
    ]
    connect.assert_called_once()
    if fails:
        assert names == expected[:2]
        check_error(response, 503, "SQL_WRITE_FAILED")
        connect.return_value.rollback.assert_called_once()
        connect.return_value.commit.assert_not_called()
    else:
        assert names == expected
        assert response.json()["data"]["items"] == [{"applied": True}]
        connect.return_value.commit.assert_called_once()


@pytest.mark.parametrize("fails", [False, True])
def test_price_history_is_laboratory_only_and_binds_parameters(setup, fails):
    from decimal import Decimal
    from app.core.database import SqlDatabase
    from app.main import create_registered_app
    from app.modules.price.operations import laboratory_price_write_operations

    station, connect, cursor, settings = setup
    operation = "RegistrarHistorialPrecioManual"
    settings.devices["allowed"] = settings.devices["allowed"].model_copy(
        update={"operations": frozenset({operation})},
    )
    cursor.nextset.return_value = False
    cursor.fetchone.return_value = (1, 1)
    payload = {"Query": operation, "parameters": {"codigoIsla": 1, "idManguera": 2, "codigoManguera": "03",
        "precio": "4.125", "fechaEnviado": "2026-11-26 12:00:00", "aplicado": False,
        "identificacionEmpleado": "LAB"}}
    denied = station.post("/v1/operations", headers=headers(station), json=payload)
    check_error(denied, 404, "OPERATION_NOT_FOUND")
    connect.assert_not_called()

    def execute(sql, *parameters):
        if "INSERT INTO" in sql:
            assert parameters == (1, 2, "03", Decimal("4.125"), "2026-11-26 12:00:00", 0, "LAB")
            if fails:
                raise pyodbc.Error("22003", "fixture")

    cursor.execute.side_effect = execute
    operations = laboratory_price_write_operations(SqlDatabase(settings, connect))
    with TestClient(create_registered_app(settings, operations)) as client:
        result = client.post("/v1/operations", headers=headers(client), json=payload)
    if fails:
        check_error(result, 503, "SQL_WRITE_FAILED")
        connect.return_value.rollback.assert_called_once()
        connect.return_value.commit.assert_not_called()
    else:
        assert result.json()["data"]["items"] == [{"applied": True}]
        connect.return_value.commit.assert_called_once()
