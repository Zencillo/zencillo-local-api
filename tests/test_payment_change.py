from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, contextmanager
from decimal import Decimal
from threading import Event, Lock
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from app.config import Device, Settings
from app.core.security import hash_secret
from app.main import create_app
from tools.payment_lab.server import create_lab_app
from app.errors import ApiError
from tools.payment_lab.attempts import PaymentAttempts
from tools.payment_lab.operations import CHANGE_INVOICE_PAYMENT, PAYMENT_ATTEMPT_STATUS


PAYMENT = {
    "operationId": "12222222-3333-4222-8333-444444444444",
    "idFacturaCliente": 70, "idFormaPago": 3, "formasPago": "Pago de prueba", "idTurno": 8,
    "codFp": "01", "valor": "89.1200000", "idDocumento": 500, "idCompania": 12,
    "idCentroVenta": 15, "codigoCara": 2, "xmlConsolidador": "<Consolidador/>",
    "xmlFactura": "<Factura/>", "sincronizada": False, "codigoIsla": 1,
    "codFpOriginal": "04", "formasPagoAcumulador": [{"codigo": "01", "valor": "89.1200000"}],
}
OLD = (4, Decimal("89.12"), "Anterior", None, None, None, None, None, None, None, None)
NEW = (1, Decimal("89.12"), "Pago de prueba", 12, 15, 2, 500,
       "<Consolidador/>", "<Factura/>", False, 1)


class SqlFixture:
    def __init__(self, failure=None, *, simultaneous=0):
        self.failure = failure
        self.current = [OLD]
        self.balance = (Decimal("89.12"), Decimal("0"))
        self.calls = 0
        self.rollbacks = 0
        self.commits = 0
        self.attempted_steps = []
        self.transaction_state = (1, 1)
        self.invoice_lock = Lock()
        self.opened = Event() if simultaneous else None
        self.resume = Event() if simultaneous else None
        self.control_changed = False
        self.voucher = ("synthetic-reference", "synthetic-approval")

    def connect(self, *, autocommit):
        assert autocommit is False
        if self.opened is not None:
            self.opened.set()
            assert self.resume.wait(timeout=5)
        return SqlConnection(self)


class SqlConnection:
    def __init__(self, fixture):
        self.fixture = fixture
        self.pending = []
        self.balance = (Decimal("0"), Decimal("0"))
        self.result = []
        self.holds_invoice_lock = False
        self.control_changed = False

    def cursor(self):
        connection = self

        class Cursor:
            def execute(self, sql, *parameters):
                fixture = connection.fixture
                if "XACT_ABORT" in sql:
                    return
                if "FROM dbo.FacturaCliente" in sql:
                    assert parameters == (70, 500, 8, 12, 15, 1)
                    if not connection.holds_invoice_lock:
                        assert "UPDLOCK" in sql and "HOLDLOCK" in sql
                        assert fixture.invoice_lock.acquire(timeout=5)
                        connection.holds_invoice_lock = True
                        connection.pending = list(fixture.current)
                        connection.balance = fixture.balance
                        connection.control_changed = fixture.control_changed
                    connection.result = connection.pending
                    return
                if "@@TRANCOUNT" in sql:
                    connection.result = [fixture.transaction_state]
                    return
                assert "EXEC dbo.sp_CambiarFormaPagoFacturaCompleto" in sql
                fixture.calls += 1
                assert sql.count("?") == len(parameters) == 19
                old_index = {"04": 0, "01": 1}[parameters[16]]
                new_index = {4: 0, 1: 1}[parameters[4]]
                assert parameters[17] == Decimal("-89.12")
                assert f'CodFp="{parameters[4]:02}"' in parameters[18]
                balance = list(connection.balance)
                for step in (1, 2, 3):
                    fixture.attempted_steps.append(step)
                    if fixture.failure == step - 1:
                        raise RuntimeError("possible sensitive driver detail")
                    if step == 1:
                        balance[old_index] += parameters[17]
                        connection.balance = tuple(balance)
                    if step == 2:
                        balance[new_index] += parameters[5]
                        connection.balance = tuple(balance)
                    if step == 3 and fixture.failure == "during_final_update":
                        old = connection.pending[0]
                        connection.pending = [(parameters[4], old[1], parameters[2], *old[3:])]
                        raise RuntimeError("update of payment rows failed after invoice change")
                    if step == 3 and fixture.failure != "postcondition":
                        connection.pending = [(
                            parameters[4], parameters[5], parameters[2], parameters[7],
                            parameters[8], parameters[9], parameters[10], parameters[11],
                            parameters[12], parameters[13], parameters[14],
                        )]
                        connection.control_changed = True
                if fixture.failure in ("transaction_lost", "procedure_committed_then_failed"):
                    fixture.transaction_state = (0, 0)
                if fixture.failure == "procedure_committed_then_failed":
                    fixture.current = connection.pending
                    fixture.balance = connection.balance
                    fixture.control_changed = connection.control_changed
                    raise RuntimeError("stored procedure returned error after own commit")

            def fetchall(self):
                return connection.result

            def fetchone(self):
                return connection.result[0]

            def nextset(self):
                if connection.fixture.failure == "late_result":
                    raise RuntimeError("driver rejected later result")
                return None

            def close(self):
                pass

        return Cursor()

    def commit(self):
        self.fixture.commits += 1
        if self.fixture.failure == "before_commit":
            raise RuntimeError("commit failed before persistence")
        self.fixture.current = self.pending
        self.fixture.balance = self.balance
        self.fixture.control_changed = self.control_changed
        if self.fixture.failure == "after_commit":
            raise RuntimeError("commit acknowledgement lost")

    def rollback(self):
        self.fixture.rollbacks += 1
        self.pending = self.fixture.current

    def close(self):
        if self.holds_invoice_lock:
            self.fixture.invoice_lock.release()
            self.holds_invoice_lock = False


@contextmanager
def client_with(fixture=None, *, allowed=True, attempts=None):
    settings = Settings(
        jwt_key="payment-testing-only-do-not-deploy-123",
        connection_string=None,
        devices={"lab": Device(
            station="lab", secret_hash=hash_secret("fixture-device"),
            operations={CHANGE_INVOICE_PAYMENT, PAYMENT_ATTEMPT_STATUS} if allowed else set(),
        )},
        station="lab",
    )
    with TemporaryDirectory() as directory:
        if fixture is not None and attempts is None:
            attempts = PaymentAttempts(Path(directory) / "payments", initialize=True)
        app = (create_app(settings) if fixture is None
               else create_lab_app(settings, connect=fixture.connect, attempts=attempts))
        with TestClient(app) as client:
            auth = client.post("/v1/auth/token", json={"device_id": "lab", "secret": "fixture-device"})
            token = auth.json()["data"]["access_token"]
            yield client, {"Authorization": f"Bearer {token}"}


def lookup(client, headers, operation_id=PAYMENT["operationId"]):
    return client.post("/v1/operations", headers=headers, json={
        "Query": PAYMENT_ATTEMPT_STATUS, "parameters": {"operationId": operation_id},
    })


def result(response):
    assert response.status_code == 200, response.text
    return response.json()["data"]["items"][0]


def request(client, headers, parameters=PAYMENT):
    return client.post("/v1/operations", headers=headers, json={
        "Query": CHANGE_INVOICE_PAYMENT, "parameters": parameters,
    })


def error(response, status, code):
    assert response.status_code == status
    assert response.json()["error"] == {"code": code}
    assert "sensitive driver detail" not in response.text


def test_write_is_blocked_in_the_normal_runtime():
    with client_with() as (client, headers):
        error(request(client, headers), 404, "OPERATION_NOT_FOUND")
        error(lookup(client, headers), 404, "OPERATION_NOT_FOUND")


def test_write_requires_explicit_device_permission():
    fixture = SqlFixture()
    with client_with(fixture, allowed=False) as (client, headers):
        error(request(client, headers), 403, "FORBIDDEN")
    assert fixture.calls == 0


@pytest.mark.parametrize("failure", [0, 1, 2, "during_final_update", "late_result", "postcondition"])
def test_invoice_and_accumulators_roll_back_on_precommit_failure(failure):
    fixture = SqlFixture(failure)
    with client_with(fixture) as (client, headers):
        response = request(client, headers)
        if failure == "postcondition":
            error(response, 409, "PAYMENT_STATE_CONFLICT")
        else:
            error(response, 503, "PAYMENT_WRITE_FAILED")
    assert fixture.current == [OLD]
    assert fixture.balance == (Decimal("89.12"), Decimal("0"))
    assert fixture.control_changed is False
    assert fixture.voucher == ("synthetic-reference", "synthetic-approval")
    assert fixture.rollbacks == 1 and fixture.commits == 0


@pytest.mark.parametrize("failure,expected", [
    ("before_commit", [OLD]), ("after_commit", [NEW]), ("transaction_lost", [OLD]),
    ("procedure_committed_then_failed", [NEW]),
])
def test_sql_and_driver_failures_near_commit_require_reconciliation(failure, expected):
    fixture = SqlFixture(failure)
    with client_with(fixture) as (client, headers):
        error(request(client, headers), 503, "WRITE_OUTCOME_UNKNOWN")
    assert fixture.current == expected
    assert fixture.control_changed is (expected == [NEW])
    assert fixture.voucher == ("synthetic-reference", "synthetic-approval")
    assert fixture.calls == 1
    assert fixture.rollbacks == 1


def test_committed_invoice_matches_duplicate_after_http_response_is_discarded():
    fixture = SqlFixture()
    with client_with(fixture) as (client, headers):
        request(client, headers)  # The client loses the first HTTP response.
        assert fixture.balance == (Decimal("0"), Decimal("89.12"))
        response = request(client, headers)
        assert result(response)["status"] == "already_applied"
    assert fixture.current == [NEW]
    assert fixture.calls == fixture.commits == 1


def test_success_reports_applied_after_commit():
    fixture = SqlFixture()
    with client_with(fixture) as (client, headers):
        result = request(client, headers)
        assert result.json()["data"]["items"][0]["status"] == "applied"
    assert fixture.current == [NEW]
    assert fixture.attempted_steps == [1, 2, 3]
    assert fixture.commits == 1


@pytest.mark.parametrize("initial", [[], [OLD, OLD], [NEW]])
def test_missing_ambiguous_or_different_confirmed_payment_does_not_write(initial):
    fixture = SqlFixture()
    fixture.current = initial
    with client_with(fixture) as (client, headers):
        parameters = {**PAYMENT, "xmlFactura": "<AnotherApprovedVoucher/>"}
        response = request(client, headers, parameters)
        error(response, 409, "PAYMENT_STATE_CONFLICT") if initial else error(
            response, 404, "INVOICE_NOT_FOUND",
        )
    assert fixture.calls == fixture.commits == 0


def test_incompatible_payment_amount_is_rejected_before_sql():
    fixture = SqlFixture()
    with client_with(fixture) as (client, headers):
        error(request(client, headers, {**PAYMENT, "valor": "90"}), 400, "INVALID_PARAMETERS")
    assert fixture.calls == fixture.commits == 0



@pytest.mark.parametrize("same_payload", [True, False])
def test_concurrent_requests_admit_only_one_sql_dispatch(same_payload):
    fixture = SqlFixture(simultaneous=2)
    second = PAYMENT if same_payload else {**PAYMENT, "xmlFactura": "<OtherVoucher/>"}
    with (client_with(fixture) as (client, headers),
          ThreadPoolExecutor(max_workers=2) as workers):
        first = workers.submit(request, client, headers)
        assert fixture.opened.wait(timeout=4)
        try:
            assert result(lookup(client, headers))["state"] == "PROCESSING"
            rejected = workers.submit(request, client, headers, second).result(timeout=4)
            error(rejected, 409, "PAYMENT_ATTEMPT_ACTIVE" if same_payload else "PAYMENT_ATTEMPT_CONFLICT")
            other = {**PAYMENT, "operationId": str(uuid4())}
            error(request(client, headers, other), 409, "PAYMENT_ATTEMPT_ACTIVE")
        finally:
            fixture.resume.set()
        assert result(first.result(timeout=5))["status"] == "applied"
        assert result(request(client, headers))["status"] == "already_applied"
    assert fixture.calls == fixture.commits == 1


def test_original_request_stays_applied_after_reversal_and_restart(tmp_path):
    fixture = SqlFixture()
    directory = tmp_path / "refund-attempts"
    ledger = PaymentAttempts(directory, initialize=True)
    reverse = {
        **PAYMENT, "operationId": str(uuid4()), "codFpOriginal": "01",
        "codFp": "04", "idFormaPago": 4, "formasPago": "Anterior",
        "xmlFactura": "<Reversal/>",
        "formasPagoAcumulador": [{"codigo": "04", "valor": PAYMENT["valor"]}],
    }
    with client_with(fixture, attempts=ledger) as (client, headers):
        for payment in (PAYMENT, reverse):
            assert result(request(client, headers, payment))["status"] == "applied"
    with client_with(fixture, attempts=PaymentAttempts(directory)) as (client, headers):
        assert result(request(client, headers))["status"] == "already_applied"
    assert fixture.current[0][0] == 4
    assert fixture.balance == (Decimal("89.12"), Decimal("0"))
    assert fixture.calls == fixture.commits == 2


def test_commit_then_sqlite_failure_requires_offline_reconciliation(tmp_path, monkeypatch):
    import sqlite3

    fixture = SqlFixture()
    directory = tmp_path / "uncertain-attempt"
    ledger = PaymentAttempts(directory, initialize=True)

    def fail_result(*_args):
        raise sqlite3.OperationalError("synthetic persistence failure")

    monkeypatch.setattr(ledger, "finish", fail_result)
    with client_with(fixture, attempts=ledger) as (client, headers):
        error(request(client, headers), 503, "WRITE_OUTCOME_UNKNOWN")
    restarted = PaymentAttempts(directory)
    with client_with(fixture, attempts=restarted) as (client, headers):
        assert result(lookup(client, headers))["state"] == "UNCERTAIN"
        error(request(client, headers), 503, "WRITE_OUTCOME_UNKNOWN")
        other = {**PAYMENT, "operationId": str(uuid4())}
        error(request(client, headers, other), 409, "PAYMENT_ATTEMPT_ACTIVE")
    assert fixture.current == [NEW]
    restarted.reconcile(PAYMENT["operationId"], "lab", "APPLIED", "LAB-151")
    with client_with(fixture, attempts=restarted) as (client, headers):
        assert result(lookup(client, headers))["result"] == "RECONCILED"
        assert result(request(client, headers))["status"] == "already_applied"
    assert fixture.calls == fixture.commits == 1


def test_missing_sqlite_after_provisioning_fails_closed(tmp_path):
    directory = tmp_path / "lost"
    ledger = PaymentAttempts(directory, initialize=True)
    fixture = SqlFixture()
    with client_with(fixture, attempts=ledger) as (client, headers):
        ledger.path.unlink()
        with pytest.raises(FileNotFoundError):
            PaymentAttempts(directory)
        error(request(client, headers), 503, "PAYMENT_LEDGER_UNAVAILABLE")
    assert fixture.calls == 0



def test_reconciliation_refuses_to_run_while_the_api_owns_the_ledger(tmp_path):
    directory = tmp_path / "payment-lock"
    ledger = PaymentAttempts(directory, initialize=True)
    fixture = SqlFixture()
    with client_with(fixture, attempts=ledger):
        with pytest.raises(RuntimeError, match="está en uso"):
            PaymentAttempts(directory).reconcile(PAYMENT["operationId"], "lab", "FAILED", "LAB-1")


def test_reference_rejects_possible_card_data_before_dispatch():
    fixture = SqlFixture()
    with client_with(fixture) as (client, headers):
        params = {**PAYMENT, "bankReference": "4111-1111-1111-1111"}
        error(request(client, headers, params), 400, "INVALID_PARAMETERS")
    assert fixture.calls == 0


def test_attempt_is_bound_to_the_authenticated_device(tmp_path):
    ledger = PaymentAttempts(tmp_path / "station-ledger", initialize=True)
    fixture = SqlFixture()
    with client_with(fixture, attempts=ledger) as (client, headers):
        payment = {**PAYMENT, "bankReference": "LAB-REF"}
        assert result(request(client, headers, payment))["state"] == "APPLIED"
        with pytest.raises(ApiError) as exc_info:
            ledger.status(PAYMENT["operationId"], "lab", "unrelated-device")
        assert exc_info.value.code == "PAYMENT_ATTEMPT_NOT_FOUND"
        with closing(ledger.connection()) as db:
            row = db.execute(
                "SELECT station,device,invoice,fingerprint,reference FROM attempts"
            ).fetchone()
        assert tuple(row)[:3] == ("lab", "lab", PAYMENT["idFacturaCliente"])
        assert len(row["fingerprint"]) == 64
        assert row["reference"] == "LAB-REF"
