from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.config import Settings
from app.errors import ApiError
from app.core.database import SqlDatabase
from app.modules.article.operations import article_operations, article_write_operations, article_statement_operations
from app.modules.article.repository import ArticleRepository
from app.modules.client.operations import client_operations, client_write_operations
from app.modules.dispatch.operations import dispatch_operations
from app.modules.invoice.operations import invoice_operations
from app.modules.license.operations import authenticate_cloud_license, initial_environment_operation, LicenseQuery, load_cloud_license, load_license_query, cloud_refresh_operation, startup_batch_operation, startup_identity_operations, shift_employee_operation, cloud_license_operation, employee_login_operation, license_operations, license_write_operations
from app.modules.bridge.operations import bridge_read_operations, bridge_write_operations
from app.modules.price.operations import price_operations, laboratory_price_write_operations
from app.modules.shift.operations import shift_operations, shift_expense_operation, shift_statement_operations
from app.router import make_router
from app.core.security import LocalAuth
from app.core.registry import Operations


def error_response(status: int, code: str, message: str):
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
    return JSONResponse(
        status_code=status, headers=headers,
        content={"success": False, "message": message, "data": None, "error": {"code": code}},
    )


def _demo_payment_operations(settings: Settings):
    if not settings.demo_cloud_refresh or not settings.connection_string:
        return {}
    import os
    from pathlib import Path

    import pyodbc
    from tools.payment_lab.attempts import PaymentAttempts
    from tools.payment_lab.operations import payment_operations

    ledger = Path(os.environ.get('ZENC_PAYMENT_ATTEMPTS', 'payment-attempts'))
    if not ledger.is_absolute():
        ledger = Path.cwd() / ledger
    initialize = not (ledger / 'attempts.sqlite3').exists()
    attempts = PaymentAttempts(ledger, initialize=initialize)
    attempts.recover()

    def sql_connect(*, autocommit=False):
        return pyodbc.connect(
            settings.connection_string,
            timeout=settings.sql_timeout,
            autocommit=autocommit,
        )

    return payment_operations(sql_connect, attempts)


def registered_operations(settings: Settings, connect=None):
    database = SqlDatabase(settings, connect)
    articles = ArticleRepository(database)
    # DEMO / http-private: registrar ops sin exigir sobre cifrado.
    demo = settings.demo_cloud_refresh
    sealed = settings.envelope_keys_path is not None
    lab = demo or sealed
    guard = load_license_query(LicenseQuery.REFRESH_DEMO_GUARD)
    return {
        **article_operations(articles),
        **article_write_operations(articles),
        **(article_statement_operations(articles, guard) if demo else {}),
        **license_operations(database),
        **(initial_environment_operation(database) if demo else {}),
        **(employee_login_operation(database) if lab else {}),
        **(cloud_license_operation(database) if lab else {}),
        **(cloud_refresh_operation(database) if demo else {}),
        **(startup_batch_operation(database) if demo else {}),
        **(shift_employee_operation(database) if lab else {}),
        **(startup_identity_operations(database) if lab else {}),
        **(dispatch_operations(database) if lab else {}),
        **(invoice_operations(database) if lab else {}),
        **license_write_operations(database),
        **shift_operations(database),
        **(shift_statement_operations(database, guard) if demo else {}),
        **(shift_expense_operation(database, guard) if demo else {}),
        **price_operations(database),
        **(laboratory_price_write_operations(database) if demo else {}),
        **(bridge_read_operations(database) if demo else {}),
        **(bridge_write_operations(database) if demo else {}),
        **(_demo_payment_operations(settings) if demo else {}),
        **client_operations(database),
        **client_write_operations(database),
    }


def create_app(settings: Settings | None = None, *, connect=None):
    settings = settings or Settings.from_env()
    return create_registered_app(settings, registered_operations(settings, connect), connect=connect)


def create_registered_app(settings: Settings, operations, *, lifespan=None, connect=None):
    app = FastAPI(title="Zencillo Local API", lifespan=lifespan)
    app.state.sql_configured = bool(settings.connection_string)
    envelope = None
    if settings.envelope_keys_path is not None:
        from app.core.local_envelope import LocalEnvelope
        envelope = LocalEnvelope(settings.envelope_keys_path)
    binding = envelope.challenge if envelope is not None else None
    database = SqlDatabase(settings, connect)
    app.include_router(make_router(
        LocalAuth(settings, binding), Operations(operations), envelope=envelope,
        database=database,
        license_loader=lambda station: load_cloud_license(database, station),
        license_authenticator=lambda company, user, password:
            authenticate_cloud_license(database, company, user, password),
    ))

    @app.get("/healthz", include_in_schema=False)
    async def health():
        return {"status": "ok"}

    @app.exception_handler(ApiError)
    async def api_error(request, exc):
        response = error_response(exc.status, exc.code, exc.message)
        if request_id := getattr(request.state, "operation_id", None):
            response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request, _exc):
        return error_response(400, "INVALID_REQUEST", "Solicitud inv\u00e1lida")

    @app.exception_handler(HTTPException)
    async def http_error(_request, exc):
        return error_response(exc.status_code, "HTTP_ERROR", "Solicitud no disponible")

    @app.exception_handler(Exception)
    async def unexpected_error(_request, _exc):
        return error_response(500, "INTERNAL_ERROR", "Error interno")

    return app
