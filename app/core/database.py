import logging
import re
from collections.abc import Callable, Iterable
from contextlib import closing
from contextvars import ContextVar
from threading import Lock
from time import perf_counter
from typing import Any

import pyodbc
from pydantic import BaseModel

from app.config import Settings
from app.core.sql_row import SqlRow
from app.errors import ApiError


logger = logging.getLogger(__name__)
request_context: ContextVar[tuple[str, str]] = ContextVar("sql_request", default=("-", "-"))

NATIVE_CODES = {
    "-2146893019": "certificate_trust",
    "-2146893022": "certificate_identity",
    "10054": "socket_reset",
    "10053": "socket_aborted",
    "10060": "socket_timeout",
    "10061": "socket_refused",
    "10051": "network_unreachable",
    "10065": "host_unreachable",
    "10048": "address_in_use",
    "10055": "socket_resources",
    "18456": "login_rejected",
    "4060": "database_unavailable",
}


def odbc_failure(error: pyodbc.Error) -> tuple[str, str, str]:
    raw_state = error.args[0] if error.args else None
    state = raw_state if isinstance(raw_state, str) and re.fullmatch(r"[A-Z0-9]{5}", raw_state) else "UNKNOWN"
    # Only emit fixed labels and allowlisted native codes, never driver text.
    detail = " ".join(str(part) for part in error.args[1:]).casefold()
    native = next((code for code in re.findall(r"\((-?\d+)\)", detail) if code in NATIVE_CODES), None)
    if native is not None:
        return state, NATIVE_CODES[native], native
    if re.search(r"certificate|certificaci|certificado", detail):
        return state, "certificate", "-"
    if re.search(r"pre.login|handshake|negociaci|ssl provider", detail):
        return state, "prelogin_or_tls", "-"
    if re.search(r"timeout|tiempo de espera", detail):
        return state, "timeout", "-"
    return state, "unclassified", "-"



class SqlDatabase:
    def __init__(self, settings: Settings, connect: Callable | None = None):
        self.settings = settings
        self.connect = connect or pyodbc.connect
        self._lock = Lock()
        self._active = 0

    def verify_login(self, user: str, password: str) -> None:
        from pydantic import SecretStr
        from app.install_station_sql import connection_string
        profile = self.settings.sql_login_profile
        if profile is None or not self.settings.connection_string:
            raise ApiError(503, "DATABASE_NOT_CONFIGURED", "SQL Server no está configurado")
        if not user or not password or any(ch in user + password for ch in "\r\n\0"):
            raise ApiError(401, "SQL_LOGIN_REJECTED", "Credenciales SQL inválidas")
        try:
            connection = connection_string(profile.model_copy(update={"user":user, "password":SecretStr(password)}))
        except ValueError:
            raise ApiError(401, "SQL_LOGIN_REJECTED", "Credenciales SQL inválidas") from None
        try:
            with closing(self.connect(connection, timeout=self.settings.sql_timeout, autocommit=True)):
                pass
        except pyodbc.Error as exc:
            state, category, _ = odbc_failure(exc)
            if state == "28000" or category == "login_rejected":
                raise ApiError(401, "SQL_LOGIN_REJECTED", "Credenciales SQL inválidas") from None
            raise ApiError(503, "SQL_UNAVAILABLE", "Conexión SQL no disponible") from None

    def read(
        self, sql: str, _legacy_model: type[BaseModel] | None = None, *, parameters: tuple[Any, ...] = (),
    ) -> list["SqlRow"]:
        """Run registered SQL and preserve every column returned by it.

        `_legacy_model` is accepted only while callers are cleaned up. It is
        intentionally not used to project or transform SQL rows.
        """
        connection_string = self.settings.connection_string
        if not connection_string or not connection_string.strip():
            raise ApiError(503, "DATABASE_NOT_CONFIGURED", "SQL Server no est\u00e1 configurado")
        with self._lock:
            self._active += 1
            active_at_start = self._active
        stage = "connect"
        started = perf_counter()
        connect_ms = None
        try:
            with closing(self.connect(
                connection_string, timeout=self.settings.sql_timeout, autocommit=True,
            )) as connection:
                connect_ms = round((perf_counter() - started) * 1000)
                stage = "cursor"
                connection.timeout = self.settings.sql_timeout
                with closing(connection.cursor()) as cursor:
                    stage = "execute"
                    cursor.execute(sql, *parameters)
                    stage = "fetch"
                    columns = [column[0] for column in cursor.description]
                    return [
                        SqlRow(zip(columns, row, strict=True))
                        for row in cursor.fetchall()
                    ]
        except pyodbc.Error as exc:
            state, category, native = odbc_failure(exc)
            request_id, operation = request_context.get()
            elapsed_ms = round((perf_counter() - started) * 1000)
            with self._lock:
                active = self._active
            logger.warning(
                "ODBC stage=%s sqlstate=%s request_id=%s operation=%s connect_ms=%d "
                "elapsed_ms=%d active_at_start=%d active=%d category=%s native=%s",
                stage, state, request_id, operation,
                elapsed_ms if connect_ms is None else connect_ms,
                elapsed_ms, active_at_start, active, category, native,
            )
            if state in {"HYT00", "HYT01", "S1T00"}:
                raise ApiError(504, "SQL_TIMEOUT", "Tiempo de espera SQL agotado") from None
            if stage != "connect" and state.startswith(("22", "42")):
                raise ApiError(502, "SQL_QUERY_FAILED", "SQL Server no pudo ejecutar la consulta") from None
            raise ApiError(503, "SQL_UNAVAILABLE", "Consulta local no disponible") from None
        except (ValueError, TypeError):
            raise ApiError(502, "SQL_RESULT_INVALID", "Formato de datos SQL inesperado") from None
        finally:
            with self._lock:
                self._active -= 1



    def read_result_sets(self, sql: str, parameters: tuple[Any, ...]) -> list[list[dict[str, Any]]]:
        connection_string = self.settings.connection_string
        if not connection_string:
            raise ApiError(503, "DATABASE_NOT_CONFIGURED", "SQL Server no está configurado")
        try:
            with closing(self.connect(
                connection_string, timeout=self.settings.sql_timeout, autocommit=True,
            )) as connection:
                connection.timeout = self.settings.sql_timeout
                with closing(connection.cursor()) as cursor:
                    cursor.execute(sql, *parameters)
                    result_sets = []
                    while True:
                        if cursor.description is not None:
                            columns = [column[0] for column in cursor.description]
                            result_sets.append([
                                dict(zip(columns, row, strict=True)) for row in cursor.fetchall()
                            ])
                        if not cursor.nextset():
                            return result_sets
        except pyodbc.Error as error:
            state, category, native = odbc_failure(error)
            request_id, operation = request_context.get()
            logger.warning("ODBC result sets request_id=%s operation=%s sqlstate=%s category=%s native=%s",
                           request_id, operation, state, category, native)
            if state in {"HYT00", "HYT01", "S1T00"}:
                raise ApiError(504, "SQL_TIMEOUT", "Tiempo de espera SQL agotado") from None
            raise ApiError(502, "SQL_QUERY_FAILED", "SQL Server no pudo ejecutar la consulta") from None

    def write(self, statements: Iterable[tuple[str, tuple[Any, ...]]], *, count_rows: bool = False, result_model: type[BaseModel] | None = None):
        """Commit one registered mutation or batch using a single connection."""
        connection_string = self.settings.connection_string
        if not connection_string:
            raise ApiError(503, "DATABASE_NOT_CONFIGURED", "SQL Server no está configurado")
        dispatched = False
        committing = False
        affected = None
        result = []
        try:
            with closing(self.connect(connection_string, timeout=self.settings.sql_timeout, autocommit=False)) as connection:
                try:
                    connection.timeout = self.settings.sql_timeout
                    with closing(connection.cursor()) as cursor:
                        cursor.execute("SET XACT_ABORT ON; SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;")
                        for sql, parameters in statements:
                            dispatched = True
                            cursor.execute(sql, *parameters)
                            if count_rows:
                                affected = cursor.rowcount
                            while True:
                                if result_model is not None and cursor.description is not None:
                                    keys = [column[0] for column in cursor.description]
                                    result.extend(result_model.model_validate(dict(zip(keys, row, strict=True)))
                                                  for row in cursor.fetchall())
                                if not cursor.nextset():
                                    break
                        cursor.execute("SELECT @@TRANCOUNT, XACT_STATE()")
                        if tuple(cursor.fetchone()) != (1, 1):
                            raise ApiError(503, "WRITE_OUTCOME_UNKNOWN", "Verifique el resultado de la escritura")
                        committing = True
                        connection.commit()
                        return result if result_model is not None else affected
                except Exception:
                    try:
                        connection.rollback()
                    except pyodbc.Error:
                        raise ApiError(503, "WRITE_OUTCOME_UNKNOWN", "Verifique el resultado de la escritura") from None
                    raise
        except pyodbc.Error as error:
            state, category, native = odbc_failure(error)
            request_id, operation = request_context.get()
            logger.warning("ODBC write request_id=%s operation=%s sqlstate=%s category=%s native=%s",
                           request_id, operation, state, category, native)
            if committing or (dispatched and (state.startswith("08") or state in {"HYT00", "HYT01", "S1T00"})):
                raise ApiError(503, "WRITE_OUTCOME_UNKNOWN", "Verifique el resultado de la escritura") from None
            raise ApiError(503, "SQL_WRITE_FAILED", "No se completó la escritura SQL") from None
