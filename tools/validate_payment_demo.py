"""Exercise the installed payment SP on disposable rows of the fixed DEMO only."""
import argparse
import asyncio
import json
import secrets
import ssl
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from decimal import Decimal
from http.client import HTTPSConnection
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from uuid import uuid4

import pyodbc

from app.config import Device, Settings
from app.core.security import hash_secret
from tools.payment_lab.server import create_lab_app
from tools.payment_lab.attempts import PaymentAttempts
from tools.payment_lab.operations import CHANGE_INVOICE_PAYMENT, PAYMENT_ATTEMPT_STATUS
from tools.demo_config import DATABASE, HOST, PORT, connection_string, require
from tools.run_concurrent_demo import post
from tools.run_flutter_windows_pilot import TestServer, certificates


TOTAL = Decimal("89.12")
MARKER = "LAB LOCAL API 15.1"
ACCOUNTS = {4: (10004, "Efectivo"), 5: (10005, "Cheque")}


def dump(value):
    return json.dumps(value, ensure_ascii=False, default=str, sort_keys=True)


def snapshot(cursor, document, turn):
    queries = {
        "factura": ("SELECT IdFormaPago, FormasPago, ValorTotalFactura, Facturada, Anulada, facturaProcesada, NumeroFactura, CodigoElectronico FROM dbo.FacturaCliente WHERE IdDocumento=? AND IdTurno=?", (document, turn)),
        "pago": ("SELECT IdCompania,IdCentroVenta,CodigoCara,IdUltimaVenta,CONVERT(nvarchar(max),XMLConsolidador),CONVERT(nvarchar(max),XMLFactura),Sincronizada,CodigoIsla FROM dbo.FormaPagoVenta WHERE IdDocumento=? AND IdTurno=?", (document, turn)),
        "detalle": ("SELECT IdFormaPago,NumeroReferencia,MontoTotal,Anulada FROM dbo.FormaPagoDetalle WHERE IdVenta=? AND IdTurno=? ORDER BY IdFormaPago", (document, turn)),
        "acumulados": ("SELECT Codigo,Valor FROM dbo.AcumuladoraFormaPago WHERE idTurno=? ORDER BY Codigo", (turn,)),
        "control": ("SELECT CambioFormaPagoVenta,SincronizoFormasPagoFacturacion,SincronizaFormasPagoConsolidacion FROM dbo.ControlProcesosPorVenta WHERE IdVenta=? AND IdTurno=?", (document, turn)),
        "turno_activo": ("SELECT IdTurno FROM dbo.TurnoEmpleado WHERE IdTurno=?", (turn,)),
    }
    return {name: [tuple(row) for row in cursor.execute(sql, *params).fetchall()]
            for name, (sql, params) in queries.items()}


def same(current, expected, label):
    if current != expected:
        raise AssertionError(label)


def drain(cursor):
    while cursor.nextset():
        pass


def scenario_state(snap, target, initial):
    same(snap["factura"], [(target, ACCOUNTS[target][1], TOTAL, True, True, True, None, None)], "Factura")
    same(snap["acumulados"], [(4, TOTAL if target == 4 else 0), (5, TOTAL if target == 5 else 0)], "Acumulados")
    same(snap["detalle"], initial["detalle"], "Detalle de voucher sintético")
    same(snap["control"], [], "Control en cola")
    same(snap["turno_activo"], [], "Turno usado")
    assert len(snap["pago"]) == 1 and snap["pago"][0][6] is True


def main(report, *, include_rollbacks=False):
    user, password = require()
    string = connection_string(user, password, verify=False)

    def connect(*, autocommit):
        return pyodbc.connect(string, timeout=6, autocommit=autocommit)

    with closing(connect(autocommit=True)) as reader, closing(reader.cursor()) as read:
        reader.timeout = 10
        identity = read.execute("""SELECT DB_NAME(),local_net_address,local_tcp_port,encrypt_option
             FROM sys.dm_exec_connections WHERE session_id=@@SPID""").fetchone()
        same(tuple(identity), (DATABASE, HOST, PORT, "TRUE"), "Destino y cifrado DEMO")
        assert not read.execute("""SELECT 1 FROM sys.triggers WHERE is_disabled=0 AND
              OBJECT_NAME(parent_id) IN ('FacturaCliente','FormaPagoVenta','FormaPagoDetalle',
              'AcumuladoraFormaPago','ControlProcesosPorVenta','TurnoEmpleado')""").fetchone()
        assert not read.execute("""SELECT 1 FROM msdb.dbo.sysjobs j JOIN msdb.dbo.sysjobsteps s ON j.job_id=s.job_id
              WHERE j.enabled=1 AND j.name <> 'syspolicy_purge_history'""").fetchone()
        company, center, island = read.execute("""SELECT TOP 1 IdCompania,IdCentroVenta,CodigoIsla
              FROM dbo.ConfiguracionInicial WHERE CodigoIsla BETWEEN 1 AND 998 ORDER BY CodigoIsla""").fetchone()
        reference = {int(row[0]): (row[1], row[2]) for row in read.execute(
            "SELECT Codigo,IdFormaPago,Nombre FROM dbo.FormaPago WHERE Codigo IN (4,5)")}
        same(reference, ACCOUNTS, "Catálogo de medios no bancarios")
        document = 1800000000 + secrets.randbelow(80000000)
        turn = document
        control_preexisting = read.execute("SELECT TOP 1 1 FROM dbo.ControlProcesosPorVenta WHERE IdVenta=? OR IdTurno=?", document, turn).fetchone()
        assert control_preexisting is None
        assert read.execute("SELECT TOP 1 IdFacturaCliente FROM dbo.FacturaCliente WHERE IdDocumento=? OR IdTurno=?", document, turn).fetchone() is None
        same(snapshot(read, document, turn), {key: [] for key in snapshot(read, document, turn)}, "Aislamiento inicial")
        evidence = {"database": DATABASE, "endpoint": f"{HOST}:{PORT}", "tls_encrypted": True,
                    "fixture": {"document": document, "turn": turn}, "checks": {}}
        report.parent.mkdir(parents=True, exist_ok=True)

        def record(label, value):
            evidence["checks"][label] = value
            report.write_text(
                json.dumps(evidence, ensure_ascii=False, default=str, indent=2, sort_keys=True) + "\n",
                encoding="utf8",
            )
            print(label, flush=True)

        seeded = False
        try:
            with closing(connect(autocommit=False)) as db, closing(db.cursor()) as c:
                c.execute("""INSERT dbo.FacturaCliente
                    (IdDocumento,IdTurno,NombreCliente,IdFormaPago,FormasPago,ValorTotalFactura,
                     Facturada,Anulada,facturaProcesada)
                    OUTPUT inserted.IdFacturaCliente VALUES (?,?,?,?,?,?,1,1,1)""",
                    document, turn, MARKER, 4, "Efectivo", TOTAL)
                invoice = c.fetchone()[0]
                c.execute("""INSERT dbo.FormaPagoDetalle
                    (IdVenta,IdTurno,IdFormaPago,NumeroReferencia,MontoTotal,Anulada)
                    VALUES (?,?,10004,?,?,1)""", document, turn, "LAB151", TOTAL)
                c.execute("""INSERT dbo.AcumuladoraFormaPago
                    (IdFormaPago,idTurno,NombreFormaPago,Valor,Codigo)
                    VALUES (10004,?,'Efectivo',?,4),(10005,?,'Cheque',0,5)""", turn, TOTAL, turn)
                seeded = True
                db.commit()
            evidence["fixture"]["invoice"] = invoice
            baseline = snapshot(read, document, turn)
            record("estado_inicial", baseline)

            def payload(target=5, *, overlap=False):
                id_fp, label = ACCOUNTS[target]
                suffix = "DISTINTO" if overlap else "ORIGINAL"
                return {
                    "idFacturaCliente": invoice, "idFormaPago": id_fp, "formasPago": label,
                    "idTurno": turn, "codFp": str(target), "valor": str(TOTAL),
                    "idDocumento": document, "idCompania": company, "idCentroVenta": center,
                    "codigoCara": 0, "xmlConsolidador": f"<Laboratorio>{suffix}</Laboratorio>",
                    "xmlFactura": f"<Laboratorio>DEMO{target}</Laboratorio>", "sincronizada": True,
                    "codigoIsla": island, "codFpOriginal": str(9 - target),
                    "formasPagoAcumulador": [{"codigo": str(target), "valor": str(TOTAL)}],
                }

            # Invoke each installed child and induce a SQL Server error while its changes remain uncommitted.
            for stop in ((1, 2, 3) if include_rollbacks else ()):
                with closing(connect(autocommit=False)) as db, closing(db.cursor()) as c:
                    db.timeout = 12
                    try:
                        c.execute("SET XACT_ABORT ON; SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;")
                        c.execute("SELECT IdFacturaCliente FROM dbo.FacturaCliente WITH (UPDLOCK,HOLDLOCK) WHERE IdFacturaCliente=?", invoice)
                        c.fetchone()
                        c.execute("""INSERT dbo.ControlProcesosPorVenta
                            (IdVenta,IdTurno,CambioFormaPagoVenta,SincronizoFormasPagoFacturacion,
                            SincronizaFormasPagoConsolidacion) VALUES (?,?,0,1,1)""", document, turn)
                        c.execute("EXEC dbo.actualizarAcumuladoraFormaPago @IdTurno=?, @CodFp=?, @Valor=?", turn, "4", -TOTAL)
                        drain(c)
                        if stop >= 2:
                            c.execute("EXEC dbo.sp_ActualizarAcumuladoraFormaPagoBatch @IdTurno=?, @FormasPagoXml=?",
                                      turn, '<FormasPago><Item CodFp="5" Valor="89.12"/></FormasPago>')
                            drain(c)
                        if stop == 3:
                            p = payload()
                            c.execute("""EXEC dbo.actualizarFacturaClienteYFormasPago
                                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?""", invoice, 10005, "Cheque", turn,
                                5, TOTAL, document, company, center, 0, document,
                                p["xmlConsolidador"], p["xmlFactura"], True, island, document, True)
                            drain(c)
                        partial = snapshot(c, document, turn)
                        same(partial["factura"][0][0], 5 if stop == 3 else 4, "Cambio dentro de transacción")
                        same(partial["acumulados"], [(4, 0), (5, TOTAL if stop >= 2 else 0)], "Acumulado parcial")
                        same(partial["control"], [(stop == 3, True, True)], "Control dentro de transacción")
                        c.execute("RAISERROR ('LAB15: fallo intencional después de etapa',16,1);")
                        drain(c)
                        raise AssertionError("Faltó error SQL inducido")
                    except pyodbc.Error as exc:
                        if "LAB15:" not in "".join(str(part) for part in exc.args):
                            raise
                        sqlstate = exc.args[0]
                    finally:
                        db.rollback()
                same(snapshot(read, document, turn), baseline, f"Rollback etapa {stop}")
                record(f"rollback_etapa_{stop}", {"sqlstate": sqlstate, "durante": partial,
                                                  "despues": baseline})

            secret = secrets.token_urlsafe(32)
            stations = {"lab": Device(
                station="demo-lab", secret_hash=hash_secret(secret),
                operations={CHANGE_INVOICE_PAYMENT, PAYMENT_ATTEMPT_STATUS},
            )}
            settings = Settings(jwt_key=secrets.token_urlsafe(48), connection_string=None,
                                devices=stations, station="demo-lab", sql_timeout=10)
            with TemporaryDirectory(prefix="payment-demo-lab-") as temp:
                folder = Path(temp)
                certificates(folder)
                tls = ssl.create_default_context(cafile=str(folder / "ca.pem"))
                directory = folder / "attempts"
                ledger = PaymentAttempts(directory, initialize=True)
                lab = None
                response_started = Event()
                hold_sql = Event()
                entered_sql = Event()
                release_sql = Event()
                sql_requests = 0

                def payment_connect(**options):
                    nonlocal sql_requests
                    sql_requests += 1
                    if hold_sql.is_set():
                        entered_sql.set()
                        assert release_sql.wait(timeout=8)
                    return connect(**options)

                def stop():
                    nonlocal lab
                    if lab:
                        lab.close()
                        lab = None

                def start(attempts):
                    nonlocal lab, token
                    stop()
                    lab = TestServer(settings, folder)
                    app = create_lab_app(settings, connect=payment_connect, attempts=attempts)

                    async def delay_success(scope, receive, send):
                        if scope["type"] != "http" or (b"x-lab-drop", b"1") not in scope["headers"]:
                            await app(scope, receive, send)
                            return

                        async def hold(message):
                            if message["type"] == "http.response.start":
                                if message["status"] == 200:
                                    response_started.set()
                                await asyncio.sleep(3)
                            await send(message)
                        await app(scope, receive, hold)

                    lab.server.config.app = delay_success
                    lab.start()
                    status, auth = post(lab.port, tls, "/v1/auth/token", {"device_id": "lab", "secret": secret})
                    assert status == 200
                    token = auth["data"]["access_token"]

                token = None

                def send(request, query=CHANGE_INVOICE_PAYMENT):
                    return post(lab.port, tls, "/v1/operations",
                                {"Query": query, "parameters": request}, token)

                def status_of(request):
                    code, body = send({"operationId": request["operationId"]}, PAYMENT_ATTEMPT_STATUS)
                    assert code == 200
                    return body["data"]["items"][0]["state"]

                def success(request, expected):
                    code, body = send(request)
                    assert code == 200, (code, body.get("error", {}).get("code"))
                    row, = body["data"]["items"]
                    same((row["operationId"], row["state"], row["status"]),
                         (request["operationId"], "APPLIED", expected), "Contrato HTTP del intento")

                def fails(request, status_code, error_code):
                    code, body = send(request)
                    same((code, body["error"]["code"]), (status_code, error_code), "Error HTTP esperado")

                a = {**payload(), "operationId": str(uuid4()), "bankReference": "DEMO-ATTEMPT-A"}
                b = {**payload(4), "operationId": str(uuid4())}
                c_attempt = {**payload(), "operationId": str(uuid4())}
                try:
                    start(ledger)
                    if include_rollbacks:
                        fails({**payload(), "operationId": str(uuid4()), "formasPago": "LAB-" + "X" * 75},
                              503, "PAYMENT_WRITE_FAILED")
                        same(snapshot(read, document, turn), baseline, "Rollback del SP orquestador")
                    prior_sql = sql_requests
                    hold_sql.set()
                    with ThreadPoolExecutor(max_workers=2) as pool:
                        first = pool.submit(success, a, "applied")
                        assert entered_sql.wait(timeout=5)
                        try:
                            same(status_of(a), "PROCESSING", "Estado concurrente")
                            pool.submit(fails, a, 409, "PAYMENT_ATTEMPT_ACTIVE").result(timeout=5)
                        finally:
                            hold_sql.clear()
                            release_sql.set()
                        first.result(timeout=10)
                    same(sql_requests, prior_sql + 1, "Un acceso SQL por intento concurrente")
                    applied = snapshot(read, document, turn)
                    scenario_state(applied, 5, baseline)
                    record("exito_y_concurrencia", {"attempt": a["operationId"], "sql_dispatches": 1,
                                                    "responses": ["applied", "PAYMENT_ATTEMPT_ACTIVE"], "after": applied})
                    success(a, "already_applied")
                    fails({**a, "xmlFactura": "<Otro/>"}, 409, "PAYMENT_ATTEMPT_CONFLICT")
                    same(sql_requests, prior_sql + 1, "Duplicado e identificador en conflicto sin SQL")
                    record("repeticion_y_conflicto", {"same": "already_applied", "different": "PAYMENT_ATTEMPT_CONFLICT"})
                    start(PaymentAttempts(directory))
                    success(a, "already_applied")
                    same(sql_requests, prior_sql + 1, "Reinicio sin reejecutar SQL")
                    record("reinicio_fastapi", {"attempt": a["operationId"], "sql_dispatches": 0})
                    with closing(HTTPSConnection("127.0.0.1", lab.port, context=tls, timeout=2)) as wire:
                        wire.request("POST", "/v1/operations",
                                     dump({"Query": CHANGE_INVOICE_PAYMENT, "parameters": b}),
                                     {"Content-Type": "application/json", "Authorization": f"Bearer {token}",
                                      "X-Lab-Drop": "1"})
                        try:
                            wire.getresponse()
                            raise AssertionError("La respuesta no se perdió")
                        except TimeoutError:
                            assert response_started.is_set(), "El timeout ocurrió antes del commit"
                    reversed_state = snapshot(read, document, turn)
                    scenario_state(reversed_state, 4, baseline)
                    same(status_of(b), "APPLIED", "Cambio confirmado tras timeout")
                    success(b, "already_applied")
                    record("respuesta_https_perdida", {"attempt": b["operationId"], "state": "APPLIED",
                                                       "retry": "already_applied", "after": reversed_state})
                    success(a, "already_applied")
                    same(sql_requests, prior_sql + 2, "El identificador antiguo no llegó a SQL")
                    same(snapshot(read, document, turn), reversed_state, "El reenvío antiguo no alteró el estado")
                    record("reenvio_antiguo_despues_de_reversion", {"attempt": a["operationId"], "sql_dispatches": 0,
                                                                   "after": reversed_state})

                    class FailingResult(PaymentAttempts):
                        def finish(self, operation_id, state, result):
                            raise sqlite3.OperationalError("Fallo controlado al persistir el resultado")

                    start(FailingResult(directory))
                    fails(c_attempt, 503, "WRITE_OUTCOME_UNKNOWN")
                    confirmed = snapshot(read, document, turn)
                    scenario_state(confirmed, 5, baseline)
                    start(PaymentAttempts(directory))
                    same(status_of(c_attempt), "UNCERTAIN", "Estado después del reinicio")
                    fails(c_attempt, 503, "WRITE_OUTCOME_UNKNOWN")
                    fails({**c_attempt, "operationId": str(uuid4())}, 409, "PAYMENT_ATTEMPT_ACTIVE")
                    same(sql_requests, prior_sql + 3, "Intento incierto sin segundo despacho")
                    same(snapshot(read, document, turn), confirmed, "Conciliación pendiente sin cambios extra")
                    record("fallo_entre_commit_y_sqlite", {"attempt": c_attempt["operationId"], "state": "UNCERTAIN",
                                                          "blocked_other_attempt": True, "after": confirmed})
                    stop()
                    PaymentAttempts(directory).reconcile(c_attempt["operationId"], "demo-lab", "APPLIED", "DEMO-SNAPSHOT")
                    start(PaymentAttempts(directory))
                    same(status_of(c_attempt), "APPLIED", "Estado conciliado")
                    success(c_attempt, "already_applied")
                    same(sql_requests, prior_sql + 3, "Conciliación y duplicado sin SQL")
                    same(snapshot(read, document, turn), confirmed, "Conciliación no escribe SQL Server")
                    record("conciliacion", {"attempt": c_attempt["operationId"], "state": "APPLIED", "sql_dispatches": 0})
                finally:
                    release_sql.set()
                    stop()
        finally:
            if seeded:
                with closing(connect(autocommit=False)) as db, closing(db.cursor()) as c:
                    c.execute("""SELECT IdFacturaCliente FROM dbo.FacturaCliente WITH(UPDLOCK,HOLDLOCK)
                        WHERE IdDocumento=? AND IdTurno=? AND NombreCliente=?""", document, turn, MARKER)
                    fixture = c.fetchone()
                    if fixture is not None:
                        assert fixture[0] == invoice
                        for table, key, value in [
                            ("FormaPagoDetalle", "IdVenta", document),
                            ("FormaPagoVenta", "IdDocumento", document),
                            ("AcumuladoraFormaPago", "idTurno", turn),
                            ("FacturaCliente", "IdFacturaCliente", invoice),
                        ]:
                            c.execute(f"DELETE dbo.{table} WHERE {key}=? AND IdTurno=?", value, turn)
                    db.commit()
                cleaned = snapshot(read, document, turn)
                same(cleaned, {key: [] for key in cleaned}, "Limpieza de claves sintéticas")
                record("limpieza_verificada", cleaned)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exercise-test-data", action="store_true", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--include-rollbacks", action="store_true")
    args = parser.parse_args()
    try:
        main(args.report, include_rollbacks=args.include_rollbacks)
    except pyodbc.Error as error:
        print("SQLSTATE:", error.args[0])
        raise SystemExit(1) from None
