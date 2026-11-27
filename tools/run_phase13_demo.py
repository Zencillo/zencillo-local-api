"""Compare Capturador's original read-only SQL to the Local API on SQL DEMO."""
import argparse
import json
import os
import shutil
import subprocess
from datetime import date, time
from contextlib import closing
from pathlib import Path
import re
import secrets
import ssl
from tempfile import TemporaryDirectory
from xml.sax.saxutils import escape

import pyodbc

from app.config import Device, Settings
from app.core.database import odbc_failure
from app.core.security import hash_secret
from app.modules.license.operations import GeneralStartup, PosStartup, ShiftStartup
from tools.demo_config import DATABASE, connection_string, require
from tools.run_concurrent_demo import post
from tools.run_flutter_windows_pilot import TestServer, certificates
from tools.run_phase6_demo import REFERENCES, json_value, multiset

STARTUP_ORDER = ("CONFIG_POS", "CONFIG_CAPTURADOR", "CONFIG_PRINT", "CONFIG_RD", "CONFIG_MEDIANET", "PUNTO_VENTA_IMPRESION",
                 "TURNO_ABIERTO", "GET_TURNO_TURNO_ZETA", "SUBSIDIO_ECUADOR", "COMBUSTIBLE", "MANGUERA_TANQUE",
                 "CONFIGURACION_REDONDEO", "CAMBIO_FORMA_DE_PAGO_POS", "FORMA_PAGO_POS", "COMBUSTIBLE_CARA",
                 "TIPO_VEHICULO", "GASTO_TIPO")

SOURCE = Path("C:/dev/capturador_mobile/packages/pos_api/lib/features")


def original(file, end, *, method=None):
    source = (SOURCE / file).read_text(encoding="utf8")
    if method is not None:
        source = source.split(method, 1)[1]
    return re.search(r"(?:return|=>|=) '''\s*(SELECT\b.*?)" + end, source, re.S)[1].strip()


def operations():
    faces = original("article/models/cara_isla_response.dart", r"\s*\$whereClause",
                     method="static String selectWithFiltersQuery")
    topology = original("article/api/query_article.dart", r"\s*'''",
                        method="String queryGetCaraIsla")
    hoses = original("article/models/manguera_tanque_cara_combustible_bd.dart",
                     r"\s*\$\{where\.isNotEmpty", method="static String readQuery")
    return [
        ("ListarManguerasPorArticuloEIsla", None,
         hoses + " AND (Articulo.IdArticulo = 15061 AND CaraIsla.CodigoIsla = '1')",
         {"nIdArt":15061,"nIsla":"1"}, False),
        ("ListarManguerasPorArticuloEIsla", None, hoses, {}, False),
        ("ListarManguerasPorArticuloEIsla", None, hoses, {"nIsla":"1"}, False),
        ("ListarManguerasPorArticuloEIsla", None,
         hoses + " AND (Articulo.IdArticulo = 2147483647 AND CaraIsla.CodigoIsla = '1')",
         {"nIdArt":2147483647,"nIsla":"1"}, False),
        ("ListarCombustiblesPorCara", "COMBUSTIBLE_CARA",
         original("article/models/combustible_cara_bd.dart", r"\s*\$\{whereClause"), {}, False),
        ("ListarManguerasTanques", "MANGUERA_TANQUE",
         original("article/models/manguera_tanque_bd.dart", r"\s*\$whereClause",
                  method="static String selectQuery"), {}, False),
        ("ListarCarasFiltradas", None, faces + " WHERE [IdIsla] = 10287",
         {"gnIsla":10287,"gnNumeroCapturador":0,"isMultiIsla":False}, False),
        ("ListarCarasFiltradas", None, faces,
         {"gnIsla":10287,"gnNumeroCapturador":0,"isMultiIsla":True}, False),
        ("ListarCarasFiltradas", None, faces + " WHERE [IdIsla] = 10287 AND [NumeroCapturador] = 2147483647",
         {"gnIsla":10287,"gnNumeroCapturador":2147483647,"isMultiIsla":False}, False),
        ("ListarCarasSurtidores", None, topology.replace("$codigoIsla","1"),
         {"codigoIsla":"1"}, True),
        ("ListarCarasSurtidores", None, topology.replace("$codigoIsla","2147483647"),
         {"codigoIsla":"2147483647"}, True),
        ("ListarConfiguracionImpresion", "CONFIG_PRINT",
         original("license/api/query_license.dart", r"\s*\$whereClause", method="String queryConfigPrint"), {}, False),
        ("ListarConfiguracionRD", "CONFIG_RD",
         original("license/api/query_license.dart", r"\s*\$whereClause", method="String queryConfiguracionRD"), {}, False),
        ("ObtenerConfiguracionMedianet", "CONFIG_MEDIANET",
         original("license/models/config_medianet_bd.dart", r"\s*\x27\x27\x27",
                  method="static String readQuery").replace("$id","1"), {}, False),
        ("ListarPuntoVentaImpresion", "PUNTO_VENTA_IMPRESION",
         original("devices/models/punto_venta_impresion_bd.dart", r"\s*\x27\x27\x27",
                  method="static String readQuery").replace("$whereClause", "Documento = '1' AND IdPuntoVenta = 10211"),
         {"idPuntoVenta":10211}, False),
        ("ConsultarTurnoAbierto", "TURNO_ABIERTO",
         "SELECT TOP 1 1 AS Existe FROM TurnoEmpleado WHERE Isla = 1 AND Abierto = 1", {"isla":1}, False),
        ("ConsultarTurnoAbierto", None,
         "SELECT TOP 1 1 AS Existe FROM TurnoEmpleado WHERE Isla = 2147483647 AND Abierto = 1",
         {"isla":2147483647}, False),
        ("ListarSubsidiosEcuador", "SUBSIDIO_ECUADOR",
         original("article/api/query_article.dart", r"\s*\x27\x27\x27", method="static String selectTop1000"), {}, False),
        ("ListarFormasPagoPOS", "FORMA_PAGO_POS",
         original("article/models/forma_pago_pos.dart", r"\s*\x27\x27\x27", method="static String selectQuery"), {}, False),
        ("ListarCambiosFormaPagoPOS", "CAMBIO_FORMA_DE_PAGO_POS",
         original("article/models/cambio_forma_pago_pos.dart", r"\s*\$whereClause", method="static String selectQuery"), {}, False),
    ]

def startup_projection(sql, fields):
    """Derive the reference projection from the original Dart SELECT."""
    select, rest = re.split(r"^\s*FROM\s*", sql, 1, flags=re.M)
    select = re.sub(r"--[^\n]*", "", select.removeprefix("SELECT"))
    expressions = {}
    for part in re.finditer(r"(?:[^,()]|\([^()]*\))+", select):
        expression = " ".join(part[0].split())
        if expression:
            column = expression.split()[-1].split(".")[-1].strip("[]")
            expressions[column] = expression
    return "SELECT " + ", ".join(expressions[name] for name in fields) + "\nFROM " + rest


def phase14_operations():
    catalog = (SOURCE.parent / "core/local_api/local_api_data_source.dart").read_text(encoding="utf8")
    key_block = catalog.split("static const _capturerKeys = {", 1)[1].split("};", 1)[0]
    keys = ", ".join(f"'{key}'" for key in re.findall(r"'([A-Z0-9_]+)'", key_block))
    capturer = (
        "SELECT Valor, Llave FROM ConfiguracionCapturador WHERE EXISTS ("
        f"SELECT 1 WHERE Llave COLLATE Latin1_General_BIN2 IN ({keys}) "
        "OR (LEFT(Llave, LEN('USA_IMPRESORA_TERMICA_ISLA_')) COLLATE Latin1_General_BIN2"
        " = 'USA_IMPRESORA_TERMICA_ISLA_' AND LEN(Llave) > LEN('USA_IMPRESORA_TERMICA_ISLA_') "
        "AND PATINDEX('%[^0-9]%', SUBSTRING(COALESCE(Llave,''), LEN('USA_IMPRESORA_TERMICA_ISLA_')+1,8000)"
        " COLLATE Latin1_General_BIN2) = 0))"
    )
    pos = original("license/api/query_license.dart", r"\s*\$whereClause",
                   method="String queryConfiguracionPOS")
    shift = original("shift/api/turno_turno_zeta_bd.dart", r"\s*\x27\x27\x27",
                     method="static String queryGetTurnoAbierto")
    general = original("license/api/query_license.dart", r"\s*\x27\x27\x27",
                       method="String queryPermisos")
    prior_heads = {
        "ListarCombustibles": "COMBUSTIBLE",
        "ListarConfiguracionRedondeo": "CONFIGURACION_REDONDEO",
        "ListarTiposVehiculo": "TIPO_VEHICULO",
        "ListarTiposGasto": "GASTO_TIPO",
    }
    prior = [
        (name, head, "SELECT " + ", ".join(f"[{column}]" for column in fields)
         + f" FROM ({query}) AS baseline", {}, False)
        for name, head in prior_heads.items()
        for query, fields in (REFERENCES[name],)
    ]
    return prior + [
        ("ListarConfiguracionOperativaPOS", "CONFIG_POS",
         startup_projection(pos, PosStartup.model_fields), {}, False),
        ("ListarConfiguracionOperativaCapturador", "CONFIG_CAPTURADOR", capturer, {}, False),
        ("ConsultarEstadoTurnoYZeta", "GET_TURNO_TURNO_ZETA",
         startup_projection(shift, ShiftStartup.model_fields).replace("$isla", "1"), {"isla": 1}, False),
        ("ConsultarEstadoTurnoYZeta", None,
         startup_projection(shift, ShiftStartup.model_fields).replace("$isla", "2147483647"),
         {"isla": 2147483647}, False),
        ("ListarConfiguracionOperativaGeneral", None,
         startup_projection(general, GeneralStartup.model_fields), {}, False),
    ]


def shift_operations():
    inventory = original("devices/models/articulo_existencia_pv_bd.dart",
                         r"\s*\x27\x27\x27", method="static String readQuery")
    expense = original("devices/models/acm_gasto_turno_bd.dart",
                       r"\s*\x27\x27\x27", method="static String readQuery({")
    bags = original("devices/models/bolsa_turno_acumulado_bd.dart",
                    r"\s*\x27\x27\x27", method="static String readQuery")
    return [
        ("ListarExistenciasPuntoVenta", None,
         inventory.replace("$filtroPV", f"art_inv.idpuntoventa = {point} AND"),
         {"idPuntoVenta": point}, False)
        for point in (10211, -1, 2147483647)
    ] + [
        ("ListarGastosAcumuladosTurno", None,
         expense.replace("$whereClause", f"WHERE gt.idturno = {turn}"),
         {"idTurno": turn}, False)
        for turn in (4422, 2147483647)
    ] + [
        ("ListarBolsasAcumuladasTurno", None,
         bags.replace("$whereClause", f"WHERE BolsasTurno.IdTurno = {turn}"),
         {"idTurno": turn}, True)
        for turn in (4494, 2147483647)
    ]


def functional_operations():
    article = original("article/models/articulo_bd.dart", r"\s*\x27\x27\x27",
                       method="static String readQuery(")
    for label, value in {"$artFilter": "= Articulo.Articulo", "$codArtFilter": "Articulo.CodigoArticulo",
                         "$estadoFilter": "Articulo.Estado"}.items():
        article = article.replace(label, value)
    reads = [
        ("ListarArticulosEstacion", None,
         article.replace(chr(36) + "{idPuntoVenta ?? 0}", str(point or 0))
                .replace("$combustibleFilter", str(int(fuel))),
         {"isCombustible": fuel, "idPuntoVenta": point}, True)
        for fuel, point in ((False, None), (False, 10211), (False, -1), (True,None))
    ]
    for name, file, turn, label in (
        ("ListarCashbackAcumuladoTurno", "acm_cash_back_turno_bd",4496,"idTurno"),
        ("ListarDescuentosAcumuladosTurno", "acm_desceunto_bd",4519,"nIdTurno"),
        ("ListarArticulosAcumuladosTurno", "acumuladora_articulo_bd",4519,"idTurno"),
        ("ListarFormasPagoAcumuladasTurno", "acumuladora_forma_pago_bd",4519,"idTurno"),
    ):
        source = (SOURCE / f"devices/models/{file}.dart").read_text(encoding="utf8")
        query = re.search(r"return \x27\x27\x27\s*(select.*?)\x27\x27\x27", source, re.S | re.I)[1]
        reads.extend((name, None, query.replace("$" + label, str(value)), {"idTurno": value},
                      file == "acumuladora_forma_pago_bd")
                     for value in (turn,2147483647))

    for name, file, marker in [('ContarFacturasTurno', 'sale/models/factura_cliente_bd.dart', 'static String countByIdTurnoQuery'), ('ConsultarVentaEspecialTurno', 'devices/api/devices_api.dart', 'String getVentaEspecialQuery'), ('ConsultarDiferenciaVentaEspecialTurno', 'devices/api/devices_api.dart', 'String getDiferenciaVentaEspecialQuery')]:
        query = original(file, r"\s*\x27\x27\x27", method=marker)
        reads.extend((name, None, query.replace("$idTurno",str(turn)), {"idTurno":turn}, False)
                     for turn in (4519,2147483647))
    reads.append(("ListarArticulosPanteraPago", None,
                  original("article/models/articulo_bd.dart", r"\s*\x27\x27\x27",
                           method="static String readPanteraPagoQuery"), {}, True))
    nozzles = original("devices/models/turno_detalle_bd.dart", r"\s*\x27\x27\x27", method="static String readQuery")
    reads.extend(("ListarLecturasMangueraTurno", None,
                  nozzles.replace("$where", f"WHERE TurnoDetalle.IdTurno = {turn}"),
                  {"idTurno":turn}, True) for turn in (4519,2147483647))
    scheduled = original(
        "price/api/query_price.dart", r"\s*\x27\x27\x27",
        method="String buildGetArticuloPrecioProgramadoQuery",
    )
    for date_value, island in (("2026-11-25T00:00:00", 1), ("2000-01-01T00:00:00", 2147483647)):
        params = {"fecha": date_value, "aplicado": 0, "horaInicio": 0, "horaFin": 0, "codigoIsla": island}
        query = scheduled
        for key, value in params.items():
            query = query.replace("$" + key, str(value))
        reads.append(("ListarPreciosProgramados", None, query, params, False))

    manual = original(
        "price/models/articulo_precio_programado_manual_bd.dart", r"\s*\x27\x27\x27",
        method="static String readQuery",
    )
    reads.append(("ListarHistorialPreciosManuales", None,
                  manual.replace("$whereClause", "WHERE AP.CodigoIsla = '2147483647'"),
                  {"codigoIsla": 2147483647}, False))
    client="client/models/cliente_offline_bd.dart"
    for name, marker, placeholder, replacement in (
        ("ConsultarClienteOffline", "static String readQuerySingle(", "'$identificacion'", "'LOCAL-API-MISSING'"),
        ("ConsultarClienteOfflinePorPlaca", "static String readQuery({", "$where", "WHERE p.Placa='LOCAL-API-MISSING'"),
        ("ConsultarClienteOfflinePorIdentificador", "static String readQueryIdentificador(", "'$identificador'", "'LOCAL-API-MISSING'"),
    ):
        query=original(client,r"\s*\x27\x27\x27",method=marker)
        reads.append((name,None,query.replace(placeholder,replacement),{"key":"LOCAL-API-MISSING"},False))
    return reads


def station_assignment_operations():
    assignment = original(
        "license/models/capturador_caras_bd.dart", r"\s*\x27\x27\x27",
        method="static String readQuery",
    )
    empty = 2147483647
    return [("ConsultarAsignacionCapturador", None,
             assignment.replace("$idIsla", str(empty)).replace("$numeroCapturador", str(empty)),
             {"idIsla": empty, "numeroCapturador": empty}, False)]


def continuation_operations():
    empty = 2147483647
    contract = original(
        "client/models/contrato_credito_bd.dart", r"\s*\x27\x27\x27",
        method="static String readQueryByIdentificacion",
    )
    factor = original(
        "article/api/query_article.dart", r"\s*\x27\x27\x27",
        method="static String getSubsidioFactor(",
    )
    prices = original(
        "devices/models/diferencia_precio_especial_bd.dart", r"\s*\x27\x27\x27",
        method="static String readQuery",
    )
    original_open = original(
        "shift/api/query_shift.dart", r"\s*\x27\x27\x27",
        method="String queryGetAllTurnoAbierto",
    ).strip().rstrip(";")
    reads = [("ConsultarContratoCreditoLocal", None,
              contract.replace("$safeIdentificacion", "ZENCILLONOCONTRACTTEST"),
              {"key": "ZENCILLONOCONTRACTTEST"}, False)]
    for article in ("00001", "NOT-A-NUMBER", ""):
        query = factor.replace("$safeIdArticulo", article).replace("$ano", "2000").replace("$mes", "1")
        reads.append(("ConsultarSubsidioEcuadorArticulo", None, query,
                      {"idArticulo": article, "ano": 2000, "mes": 1}, False))
    for turn in (4519, empty):
        reads.append(("ListarDiferenciasPrecioEspecialTurno", None, prices.replace("$idTurno", str(turn)),
                      {"idTurno": turn}, True))
    for turn in (4519, empty):
        reads.append(("ListarHistorialPresetsTurno", None,
                      f"SELECT * FROM HistorialPreset WHERE IdTurno = {turn}", {"idTurno": turn}, False))
    for island in (1, empty):
        query = original_open.replace("${islas.join(',')}", str(island))
        reads.append(("ConsultarExisteTurnoAbiertoIsla", None,
                      f"SELECT CAST(CASE WHEN EXISTS ({query}) THEN 1 ELSE 0 END AS INT) AS Abierto",
                      {"isla": island}, False))
    return reads


def sql_json_value(value):
    return value.isoformat() if isinstance(value, (date, time)) else json_value(value)


def read_rows(cursor):
    columns = [entry[0] for entry in cursor.description]
    return columns, [{key: sql_json_value(value) for key, value in zip(columns, row, strict=True)}
                     for row in cursor.fetchall()]


def compare(reference, actual, ordered):
    return (multiset(reference) == multiset(actual)
            and (not ordered or [multiset([row]) for row in reference] == [multiset([row]) for row in actual]))


def compare_batch(cursor, batch, reference):
    if not batch:
        return
    cursor.execute("SELECT OBJECT_ID(N'dbo.SP_EJECUTAR_QUERIES_BATCH',N'P')")
    if cursor.fetchone()[0] is None:
        print("Batch SQL: procedimiento no visible en DEMO.")
        return
    request = "<Request>" + "".join(
        f"<Item><Head>{head}</Head><Query>{escape(query)}</Query></Item>"
        for _, head, query, _, _ in batch
    ) + "</Request>"
    try:
        cursor.execute("EXEC dbo.SP_EJECUTAR_QUERIES_BATCH @Request=?", request)
        _, manifest = read_rows(cursor)
        assert [(item["Id"], item["Head"]) for item in manifest] == [
            (index, entry[1]) for index, entry in enumerate(batch, 1)
        ]
        for name, head, _, params, ordered in batch:
            assert cursor.nextset()
            columns, rows = read_rows(cursor)
            expected_columns, expected = reference[name, tuple(params.items())]
            assert columns == expected_columns and compare(expected, rows, ordered), head
        assert not cursor.nextset()
    except pyodbc.Error as exc:
        print(f"Batch SQL no validado: {odbc_failure(exc)}")
        return
    print(f"Batch SQL: manifiesto en orden y {len(batch)} conjuntos equivalentes.")


def collect(connection, reads):
    reference = {}
    with closing(pyodbc.connect(connection, timeout=6, autocommit=True)) as db, closing(db.cursor()) as cursor:
        db.timeout = 8
        cursor.execute("SELECT DB_NAME()")
        if cursor.fetchone()[0] != DATABASE:
            raise ValueError("Base DEMO distinta de la autorizada.")
        for name, _, sql, params, _ in reads:
            cursor.execute(sql)
            reference[name, tuple(params.items())] = read_rows(cursor)
        batch = {entry[1]: entry for entry in reads if entry[1]}
        compare_batch(cursor, [batch[head] for head in STARTUP_ORDER if head in batch], reference)
    return reference


def verify_http(connection, reads, reference, *, flutter=False):
    secret = secrets.token_urlsafe(32)
    settings = Settings(
        jwt_key=secrets.token_urlsafe(48), connection_string=connection, station="demo-phase13",
        devices={"demo-read": Device(station="demo-phase13", secret_hash=hash_secret(secret),
                                     operations={entry[0] for entry in reads})},
    )
    with TemporaryDirectory(prefix="zencillo-phase13-") as directory:
        folder = Path(directory)
        certificates(folder)
        tls = ssl.create_default_context(cafile=str(folder / "ca.pem"))
        server = TestServer(settings, folder)
        try:
            server.start()
            status, login = post(server.port, tls, "/v1/auth/token", {"device_id":"demo-read","secret":secret})
            assert status == 200
            token = login["data"]["access_token"]
            for name, _, _, params, ordered in reads:
                columns, original_rows = reference[name, tuple(params.items())]
                status, body = post(server.port, tls, "/v1/operations", {"Query":name,"parameters":params}, token)
                assert status == 200, (name, status, body.get("error", {}).get("code"))
                rows = body["data"]["items"]
                assert all(set(row) == set(columns) for row in rows), (name, columns, list(rows[0]))
                assert compare(original_rows, rows, ordered), name
                nulls = sum(value is None for row in rows for value in row.values())
                print(f"{name} HTTP 200: {len(rows)} filas, {len(columns)} columnas, {nulls} NULL equivalentes.")
            if flutter:
                launcher = shutil.which("flutter.bat")
                if launcher is None:
                    raise RuntimeError("Flutter no está disponible.")
                fixture = [
                    {"name": name, "head": head, "parameters": params, "ordered": ordered,
                     "rows": reference[name, tuple(params.items())][1]}
                    for name, head, _, params, ordered in reads
                ]
                ranks = {head: index for index, head in enumerate(STARTUP_ORDER)}
                fixture.sort(key=lambda entry: ranks.get(entry["head"], len(ranks)))
                (folder / "dart-fixture.json").write_text(json.dumps(fixture), encoding="utf8")
                (folder / "origin.txt").write_text(f"https://127.0.0.1:{server.port}", encoding="ascii")
                subprocess.run(
                    [launcher, "test", "--no-pub", "test/core/local_api_phase13_live_test.dart"],
                    cwd=SOURCE.parents[3],
                    env={**os.environ, "ZENC_PHASE13_FIXTURE": str(folder), "ZENC_PHASE13_SECRET": secret},
                    check=True, timeout=90,
                )
        finally:
            server.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-demo-sql-exception", action="store_true")
    parser.add_argument("--flutter", action="store_true")
    parser.add_argument("--phase14", action="store_true", help="Incluye las proyecciones de arranque.")
    parser.add_argument("--shift-reads", action="store_true", help="Valida el bloque de lecturas de turno.")
    parser.add_argument("--functional-reads", action="store_true")
    parser.add_argument("--station-assignments", action="store_true")
    parser.add_argument("--continuation-reads", action="store_true")
    args = parser.parse_args()
    user, password = require()
    connection = connection_string(user, password)
    reads = shift_operations() if args.shift_reads else operations()
    if args.functional_reads:
        reads = functional_operations()
    if args.station_assignments:
        reads = station_assignment_operations()
    if args.continuation_reads:
        reads = continuation_operations()
    if args.phase14:
        reads += phase14_operations()
    try:
        reference = collect(connection, reads)
    except pyodbc.Error as exc:
        if not args.allow_demo_sql_exception or odbc_failure(exc)[1] != "certificate_trust":
            raise SystemExit(f"SQL DEMO: {odbc_failure(exc)}") from None
        print("Excepción de certificado autorizada solo para el salto SQL DEMO.")
        connection = connection_string(user, password, verify=False)
        try:
            reference = collect(connection, reads)
        except pyodbc.Error as failure:
            raise SystemExit(f"SQL DEMO: {odbc_failure(failure)}") from None
    verify_http(connection, reads, reference, flutter=args.flutter)


if __name__ == "__main__":
    main()
