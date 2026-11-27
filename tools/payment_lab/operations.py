import hashlib
import json
import sqlite3
from collections.abc import Callable
from contextlib import closing
from decimal import Decimal
from importlib.resources import files
from typing import Annotated, Literal
from xml.etree.ElementTree import Element, SubElement, tostring

from pydantic import BaseModel, Field, model_validator

from app.core.registry import Operation, request_actor
from tools.payment_lab.attempts import PaymentAttempts, REFERENCE, UUID4
from app.errors import ApiError
from app.schemas import StrictModel


CHANGE_INVOICE_PAYMENT = "CambiarFormaPagoFactura"
PAYMENT_ATTEMPT_STATUS = "ConsultarIntentoCambioFormaPago"
PositiveInt = Annotated[int, Field(gt=0, le=2147483647)]
SqlInt = Annotated[int, Field(ge=0, le=2147483647)]
PaymentCode = Annotated[str, Field(pattern=r"^[0-9]{1,10}$")]
Amount = Annotated[str, Field(pattern=r"^[0-9]{1,10}(\.[0-9]{1,7})?$")]


class PaymentSplit(StrictModel):
    codigo: PaymentCode
    valor: Amount


class AttemptId(StrictModel):
    operationId: str = Field(pattern=UUID4)


class ChangeInvoicePayment(AttemptId):
    bankReference: str | None = Field(default=None, pattern=REFERENCE)
    idFacturaCliente: PositiveInt
    idFormaPago: PositiveInt
    formasPago: str = Field(min_length=1, max_length=200)
    idTurno: PositiveInt
    codFp: PaymentCode
    valor: Amount
    idDocumento: PositiveInt
    idCompania: PositiveInt
    idCentroVenta: PositiveInt
    codigoCara: SqlInt
    xmlConsolidador: str = Field(min_length=1, max_length=65536)
    xmlFactura: str = Field(min_length=1, max_length=65536)
    sincronizada: bool
    codigoIsla: PositiveInt
    codFpOriginal: PaymentCode
    formasPagoAcumulador: list[PaymentSplit] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def amounts_match(self):
        if self.bankReference and sum(ch.isdigit() for ch in self.bankReference) >= 12:
            raise ValueError("Use una referencia de operación, sin números de tarjeta")
        total = Decimal(self.valor)
        codes = [self.codFpOriginal, self.codFp,
                 *(split.codigo for split in self.formasPagoAcumulador)]
        amounts = [Decimal(split.valor) for split in self.formasPagoAcumulador]
        if (any(int(code) > 2147483647 for code in codes)
                or self.formasPagoAcumulador[0].codigo != self.codFp
                or total <= 0 or any(amount <= 0 for amount in amounts)
                or sum(amounts) != total):
            raise ValueError("Importes o códigos de forma de pago incompatibles")
        return self


class PaymentChangeResult(BaseModel):
    status: Literal["applied", "already_applied"]


class AttemptStatus(BaseModel):
    operationId: str
    state: Literal["PENDING", "PROCESSING", "APPLIED", "FAILED", "UNCERTAIN"]
    result: str | None = None


class DurablePaymentResult(AttemptStatus):
    status: Literal["applied", "already_applied"]


def fingerprint(payment):
    payload = payment.model_dump(exclude={"operationId"})
    payload["valor"] = format(Decimal(payload["valor"]).normalize(), "f")
    for split in payload["formasPagoAcumulador"]:
        split["valor"] = format(Decimal(split["valor"]).normalize(), "f")
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def payment_operations(lab_connect: Callable | None = None, attempts: PaymentAttempts | None = None) -> dict[str, Operation]:
    if (lab_connect is None) != (attempts is None):
        raise ValueError("El laboratorio de pagos requiere conexión y un registro durable.")

    def change_invoice_payment(**parameters):
        if lab_connect is None:
            raise ApiError(503, "PAYMENT_WRITE_DISABLED", "Cambio de pago local bloqueado")
        payment = ChangeInvoicePayment.model_validate(parameters)
        operation_id = payment.operationId
        station, device = request_actor.get()
        try:
            state = attempts.claim(operation_id, station, device, payment.idFacturaCliente,
                                   fingerprint(payment), payment.bankReference)
        except sqlite3.Error:
            raise ApiError(503, "PAYMENT_LEDGER_UNAVAILABLE", "Registro de intentos no disponible") from None
        if state == "APPLIED":
            return [DurablePaymentResult(operationId=operation_id, state=state, status="already_applied")]
        if state == "FAILED":
            raise ApiError(409, "PAYMENT_ATTEMPT_FAILED", "El intento ya terminó con fallo")
        if state in {"PENDING", "PROCESSING"}:
            raise ApiError(409, "PAYMENT_ATTEMPT_ACTIVE", "El intento ya está registrado")
        if state == "UNCERTAIN":
            raise ApiError(503, "WRITE_OUTCOME_UNKNOWN", "Conciliar el estado del cambio de pago")

        def finish(state, result):
            try:
                attempts.finish(operation_id, state, result)
            except sqlite3.Error:
                try:
                    attempts.finish(operation_id, "UNCERTAIN", "WRITE_OUTCOME_UNKNOWN")
                except sqlite3.Error:
                    pass
                raise ApiError(503, "WRITE_OUTCOME_UNKNOWN", "Conciliar el estado del cambio de pago") from None

        try:
            sql_result = change_payment(payment, lab_connect)
            if sql_result.status != "applied":
                # Current SQL state cannot attest that this new attempt made the change.
                raise ApiError(503, "WRITE_OUTCOME_UNKNOWN", "Conciliar el estado del cambio de pago")
        except ApiError as error:
            finish("UNCERTAIN" if error.code == "WRITE_OUTCOME_UNKNOWN" else "FAILED", error.code)
            raise
        except Exception:
            finish("UNCERTAIN", "WRITE_OUTCOME_UNKNOWN")
            raise ApiError(503, "WRITE_OUTCOME_UNKNOWN", "Conciliar el estado del cambio de pago") from None
        finish("APPLIED", "SQL_COMMITTED")
        return [DurablePaymentResult(operationId=operation_id, state="APPLIED", status="applied")]

    def status(operationId):
        if attempts is None:
            raise ApiError(503, "PAYMENT_WRITE_DISABLED", "Cambio de pago local bloqueado")
        station, device = request_actor.get()
        try:
            state, result = attempts.status(operationId, station, device)
        except sqlite3.Error:
            raise ApiError(503, "PAYMENT_LEDGER_UNAVAILABLE", "Registro de intentos no disponible") from None
        return [AttemptStatus(operationId=operationId, state=state, result=result)]

    return {
        CHANGE_INVOICE_PAYMENT: (ChangeInvoicePayment, change_invoice_payment),
        PAYMENT_ATTEMPT_STATUS: (AttemptId, status),
    }


def change_payment(payment: ChangeInvoicePayment, connect: Callable) -> PaymentChangeResult:
    queries = files(__package__).joinpath("queries")
    state_query = queries.joinpath("invoice_payment_state.sql").read_text(encoding="utf8")
    write_query = queries.joinpath("change_invoice_payment.sql").read_text(encoding="utf8")
    total = Decimal(payment.valor)
    new_code = int(payment.codFp)
    expected_state = (payment.formasPago, payment.idCompania, payment.idCentroVenta,
                      payment.codigoCara, payment.idDocumento, payment.xmlConsolidador,
                      payment.xmlFactura, payment.sincronizada, payment.codigoIsla)
    identity = (payment.idFacturaCliente, payment.idDocumento, payment.idTurno,
                payment.idCompania, payment.idCentroVenta, payment.codigoIsla)

    root = Element("FormasPago")
    for split in payment.formasPagoAcumulador:
        SubElement(root, "Item", CodFp=split.codigo, Valor=split.valor)

    write_started = False
    commit_started = False
    try:
        with closing(connect(autocommit=False)) as connection:
            try:
                with closing(connection.cursor()) as cursor:
                    cursor.execute("SET XACT_ABORT ON; SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;")
                    cursor.execute(state_query, *identity)
                    rows = cursor.fetchall()
                    if not rows:
                        raise ApiError(404, "INVOICE_NOT_FOUND", "Factura no encontrada")
                    if len(rows) != 1:
                        raise ApiError(409, "PAYMENT_STATE_CONFLICT", "Estado de pago ambiguo")
                    current_code, current_total, *state = rows[0]
                    if current_total != total:
                        raise ApiError(409, "PAYMENT_STATE_CONFLICT", "El total de la factura cambió")
                    if current_code == new_code and tuple(state) == expected_state:
                        connection.rollback()
                        return PaymentChangeResult(status="already_applied")
                    if current_code == new_code or current_code != int(payment.codFpOriginal):
                        raise ApiError(409, "PAYMENT_STATE_CONFLICT", "La forma de pago de la factura cambió")
                    cursor.execute("SELECT @@TRANCOUNT, XACT_STATE()")
                    if tuple(cursor.fetchone()) != (1, 1):
                        raise ApiError(503, "PAYMENT_TRANSACTION_INVALID", "Transacción SQL no disponible")
                    write_started = True
                    cursor.execute(
                        write_query, payment.idFacturaCliente, payment.idFormaPago, payment.formasPago,
                        payment.idTurno, new_code, total, payment.idDocumento, payment.idCompania,
                        payment.idCentroVenta, payment.codigoCara, payment.idDocumento,
                        payment.xmlConsolidador, payment.xmlFactura, payment.sincronizada,
                        payment.codigoIsla, payment.idDocumento, payment.codFpOriginal, -total,
                        tostring(root, encoding="unicode"),
                    )
                    # SQL Server can report errors in later ODBC result sets.
                    while cursor.nextset():
                        pass
                    cursor.execute("SELECT @@TRANCOUNT, XACT_STATE()")
                    if tuple(cursor.fetchone()) != (1, 1):
                        raise ApiError(503, "WRITE_OUTCOME_UNKNOWN", "Conciliar el estado del cambio de pago")
                    cursor.execute(state_query, *identity)
                    persisted = cursor.fetchall()
                    if len(persisted) != 1 or tuple(persisted[0]) != (new_code, total, *expected_state):
                        raise ApiError(409, "PAYMENT_STATE_CONFLICT", "La factura no refleja el cambio completo")
                    commit_started = True
                    connection.commit()
            except Exception:
                transaction_intact = not write_started
                if write_started and not commit_started:
                    try:
                        with closing(connection.cursor()) as cursor:
                            cursor.execute("SELECT @@TRANCOUNT, XACT_STATE()")
                            count, state = cursor.fetchone()
                            transaction_intact = count == 1 and state in (-1, 1)
                    except Exception:
                        transaction_intact = False
                try:
                    connection.rollback()
                except Exception:
                    transaction_intact = False
                if not transaction_intact:
                    raise ApiError(503, "WRITE_OUTCOME_UNKNOWN", "Conciliar el estado del cambio de pago") from None
                raise
    except ApiError:
        raise
    except Exception:
        if commit_started:
            raise ApiError(503, "WRITE_OUTCOME_UNKNOWN", "Conciliar el estado del cambio de pago") from None
        raise ApiError(503, "PAYMENT_WRITE_FAILED", "No se completó el cambio de pago") from None
    return PaymentChangeResult(status="applied")
