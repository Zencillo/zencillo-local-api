import hmac
from uuid import uuid4

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError

from app.errors import ApiError
from app.schemas import DeviceLicenseLogin, LicenseBootstrap, Login, OperationRequest, SqlLogin
from app.core.security import LocalAuth
from app.core.registry import Operations


def success(data: dict):
    return {"success": True, "message": "Operación completada", "data": data}


def validate(model, body):
    try:
        return model.model_validate(body)
    except ValidationError:
        raise ApiError(400, "INVALID_REQUEST", "Solicitud inválida") from None


def make_router(auth: LocalAuth, operations: Operations, *, envelope=None, database=None,
                license_loader=None, license_authenticator=None):
    router = APIRouter(prefix="/v1")
    bearer = HTTPBearer(auto_error=False)

    @router.get("/auth/challenge")
    def challenge(response: Response):
        if envelope is None:
            raise ApiError(404, "OPERATION_NOT_FOUND", "Operación desconocida")
        response.headers["Cache-Control"] = "no-store"
        return success({"challenge": envelope.challenge})

    @router.post("/auth/token")
    def login(body: dict, response: Response):
        response.headers["Cache-Control"] = "no-store"
        secret = None
        if envelope is not None:
            body, secret, request_id = envelope.open(body, "login", envelope.challenge)
        if "licenseUser" in body and "secret" not in body:
            login = validate(DeviceLicenseLogin, body)
            if license_authenticator is None:
                raise ApiError(404, "OPERATION_NOT_FOUND", "Operación desconocida")
            station = license_authenticator(
                int(login.licenseCompany), login.licenseUser,
                login.licensePassword.get_secret_value())
            token = auth.issue_validated(login.device_id, station)
            result = success({
                "access_token": token, "token_type": "Bearer",
                "expires_in": auth.settings.token_seconds,
            })
            return result if envelope is None else envelope.seal(result, secret)
        if auth.settings.sql_login_required:
            login = validate(SqlLogin, body)
        else:
            login = validate(Login, body)

        def verify():
            if envelope is not None:
                envelope.accept("login", envelope.challenge, request_id)
            if auth.settings.sql_login_required:
                database.verify_login(login.sqlUser, login.sqlPassword.get_secret_value())
            supplied = (login.licenseCompany, login.licenseUser, login.licensePassword)
            if any(value is not None for value in supplied):
                if any(value is None for value in supplied) or license_loader is None:
                    raise ApiError(400, "INVALID_REQUEST", "Solicitud inválida")
                device = auth.settings.devices.get(login.device_id)
                company, stored = license_loader(device.station)
                if (login.licenseCompany != str(company) or
                        not hmac.compare_digest(login.licenseUser, stored.UsuarioLicencia) or
                        not hmac.compare_digest(login.licensePassword.get_secret_value(),
                                                stored.ContrasenaLicencia)):
                    raise ApiError(401, "LICENSE_LOGIN_REJECTED",
                                   "Credenciales de licenciamiento inválidas")

        token = auth.issue(login.device_id, login.secret.get_secret_value(), verify)
        result = success({
            "access_token": token, "token_type": "Bearer",
            "expires_in": auth.settings.token_seconds,
        })
        return result if envelope is None else envelope.seal(result, secret)

    @router.post("/auth/license")
    def startup_license(body: dict, response: Response):
        response.headers["Cache-Control"] = "no-store"
        if license_loader is None:
            raise ApiError(404, "OPERATION_NOT_FOUND", "Operación desconocida")
        secret = None
        if envelope is not None:
            body, secret, request_id = envelope.open(body, "login", envelope.challenge)
        validate(LicenseBootstrap, body)
        if envelope is not None:
            envelope.accept("login", envelope.challenge, request_id)
        company, license = license_loader(auth.settings.station)
        result = success({"idCompany": company, "user": license.UsuarioLicencia,
                          "password": license.ContrasenaLicencia})
        return result if envelope is None else envelope.seal(result, secret)

    @router.post("/operations")
    def execute(
        body: dict,
        request: Request,
        response: Response,
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ):
        if credentials is None:
            raise ApiError(401, "UNAUTHENTICATED", "Se requiere token local")
        request_id = uuid4().hex
        request.state.operation_id = request_id
        response.headers["X-Request-ID"] = request_id
        response.headers["Cache-Control"] = "no-store"
        device, device_id = auth.authenticate(credentials.credentials)
        secret = None
        if envelope is not None:
            body, secret, nonce = envelope.open(body, "operations", credentials.credentials)
            envelope.accept("operations", credentials.credentials, nonce)
        payload = validate(OperationRequest, body)
        result = success(operations.run(payload, device, request_id, device_id))
        return result if envelope is None else envelope.seal(result, secret)

    return router
