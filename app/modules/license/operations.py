from typing import Literal

import hmac
from html import unescape
from xml.etree.ElementTree import Element, SubElement, fromstring, tostring
from enum import Enum
from functools import cache
from importlib.resources import files


from pydantic import BaseModel, Field, SecretStr

from app.core.database import SqlDatabase
from app.core.registry import Operation, request_actor
from app.errors import ApiError
from app.modules.article.operations import ExpenseTypeReplace, SqlAffectedRows, VehicleTypeReplace
from app.modules.article.repository import ArticleQuery, load_query
from app.modules.article.repository import ArticleRepository
from app.modules.article.operations import article_operations
from app.schemas import NoParameters, SqlScalar, StrictModel, WriteResult


class LicenseQuery(Enum):
    SHIFT_EMPLOYEE = "shift_employee.sql"
    STARTUP_TERMINAL = "startup_terminal.sql"
    STARTUP_SHIFT_IDENTITY = "startup_shift_identity.sql"
    CLOUD_LICENSE = "cloud_license.sql"
    EMPLOYEE_LOGIN = "employee_login.sql"
    PRINTER_CONFIG = "printer_configuration.sql"
    RD_CONFIG = "rd_configuration.sql"
    MEDIANET_CONFIG = "medianet_configuration.sql"
    PRINT_SALE_POINTS = "printing_sale_points.sql"
    PRINT_SALE_POINT = "printing_sale_point.sql"
    OPEN_SHIFT = "open_shift.sql"
    GENERAL_STARTUP = "general_startup.sql"
    SHIFT_STARTUP = "shift_startup.sql"
    POS_STARTUP = "pos_startup.sql"
    CAPTURER_STARTUP = "capturer_startup.sql"
    CAPTURER_ASSIGNMENT = "capturer_assignment.sql"
    REFRESH_DEMO_GUARD = "refresh_demo_guard.sql"
    REFRESH_CAPTURER = "refresh_capturer.sql"
    REFRESH_PAYMENT = "refresh_payment.sql"
    UPDATE_CAPTURER_SETTING = "update_capturer_setting.sql"
    UPSERT_CAPTURER_SETTING = "upsert_capturer_setting.sql"
    UPDATE_INITIAL_SETTINGS = "update_initial_settings.sql"
    DELETE_CERTIFIER_SETTING = "delete_certifier_setting.sql"
    INSERT_CAPTURER_SETTING = "insert_capturer_setting.sql"
    INSERT_CERTIFIER_SETTING = "insert_certifier_setting.sql"
    INSERT_LOYALTY_TYPE = "insert_loyalty_type.sql"
    LIST_LOYALTY_TYPES = "list_loyalty_types.sql"
    UPDATE_INITIAL_ENVIRONMENT = "update_initial_environment.sql"
    REFRESH_INITIAL = "refresh_initial.sql"
    UPSERT_ZETA_CONFIG = "upsert_zeta_config.sql"
    UPSERT_ECUADOR_SETTING = "upsert_ecuador_setting.sql"


@cache
def load_license_query(query: LicenseQuery) -> str:
    if not isinstance(query, LicenseQuery):
        raise TypeError("Se requiere una consulta de configuración registrada.")
    return files(__package__).joinpath("queries", query.value).read_text(encoding="utf8").strip()


class PrintSalePointParameters(StrictModel):
    idPuntoVenta: int = Field(ge=-2147483648, le=2147483647)


class OpenShiftParameters(StrictModel):
    isla: int | None = Field(default=None, ge=-2147483648, le=2147483647)


class CapturerAssignmentParameters(StrictModel):
    idIsla: int = Field(ge=-2147483648, le=2147483647)
    numeroCapturador: int = Field(ge=-2147483648, le=2147483647)


class CapturerAssignment(BaseModel):
    IdCapturadorCaras: SqlScalar
    IdIsla: SqlScalar
    NumeroCapturador: SqlScalar
    Puerto: SqlScalar
    IP: SqlScalar


class PrinterConfig(BaseModel):
    Isla: int | None
    IpImpresora: str | None
    Puerto: int | None
    NombreImpresora: str | None


class RdConfig(BaseModel):
    IdConfiguracionRD: int | None
    IdConfiguracionPOS: str | int | None
    CodigoComprobanteFacAutomatica: str | int | None
    VentaTodosLosPos: int | None


class MedianetConfig(BaseModel):
    id: int | None
    ip: str | None
    mascara: str | None
    gateway: str | None
    hostPrinciR1Ip: str | None
    hostPrinciR1Puerto: str | int | None
    hostAlterR1Ip: str | None
    hostAlterR1Puerto: str | int | None
    hostPrinciR2Ip: str | None
    hostPrinciR2Puerto: str | int | None
    hostAlterR2Ip: str | None
    hostAlterR2Puerto: str | int | None
    puertoEscucha: str | int | None


class PrintSalePoint(BaseModel):
    IdCompania: int | None
    IdCentroVenta: int | None
    IdPuntoVenta: int | None
    Documento: int | str | None
    Posicion: int | None
    PosicionFinal: int | None


class ShiftOpenFlag(BaseModel):
    Existe: int



class CapturerStartup(BaseModel):
    Valor: SqlScalar
    Llave: str


class PosStartup(BaseModel):
    CodigoPunto: SqlScalar
    IdCompania: SqlScalar
    IdPuntoVenta: SqlScalar
    CodigoIsla: SqlScalar
    NumeroPunto: SqlScalar
    Descripcion: SqlScalar
    AplicaSAP: SqlScalar
    Mascara: SqlScalar
    GateWay: SqlScalar
    ConsecutivoVentaEstacion: SqlScalar
    ImprimirCierreTurno: SqlScalar
    LecturasMangueras: SqlScalar
    Combustibles: SqlScalar
    Canastilla: SqlScalar
    FormasPago: SqlScalar
    Consignaciones: SqlScalar
    ManejaPinPad: SqlScalar
    IP: SqlScalar
    Puerto: SqlScalar
    RedTransaccionalBancaria: SqlScalar
    IdConfiguracion: SqlScalar
    IPCapturador: SqlScalar
    PuertoEnvio: SqlScalar
    NumReintentos: SqlScalar
    TiempoEspera: SqlScalar
    ComPinPad: SqlScalar
    ComParidad: SqlScalar
    ComBitDato: SqlScalar
    ComBitParada: SqlScalar
    ComVelocidad: SqlScalar
    TipoConexionPinPad: SqlScalar
    TamanoLetraImpresion: SqlScalar
    TypeDataphone: SqlScalar


class ShiftStartup(BaseModel):
    IdTurno: SqlScalar
    FechaZeta: SqlScalar
    Isla: SqlScalar
    FechaTurno: SqlScalar
    HoraAperturaTurno: SqlScalar
    HoraCierreTurno: SqlScalar
    Abierto: SqlScalar
    SincronizoAperturaTurno: SqlScalar
    SincronizoCierreTurno: SqlScalar
    NumeroDeTurno: SqlScalar
    SincronizoLecturasInicialesTurno: SqlScalar
    SincronizoLecturasFinalesTurno: SqlScalar
    SincronizoTotalOperacionesTurno: SqlScalar
    FechaCierreTurno: SqlScalar
    IdJornadaZeta: SqlScalar
    FechaJornadaZeta: SqlScalar
    HoraAperturaJornadaZeta: SqlScalar
    HoraCierreJornadaZeta: SqlScalar
    JornadaZetaAbierta: SqlScalar
    SincronizoAperturaJornadaZeta: SqlScalar
    SincronizoCierreJornadaZeta: SqlScalar
    SincronizoLecturasInicialesJornadaZeta: SqlScalar
    SincronizoLecturasFinalesJornadaZeta: SqlScalar
    SincronizoTotalOperacionesJornadaZeta: SqlScalar
    ManejaConsola: SqlScalar
    GuardaVariacion: SqlScalar
    CodCapturadorApertura: SqlScalar


class GeneralStartup(BaseModel):
    IdCompania: SqlScalar
    IdCentroVenta: SqlScalar
    idCVFacturacion: SqlScalar
    idPVFacturacion: SqlScalar
    CodigoIsla: SqlScalar
    IPServidor: SqlScalar
    SocketEnvio: SqlScalar
    ComReintentosNum: SqlScalar
    ComReintentosTiempo: SqlScalar
    SocketEscucha: SqlScalar
    ImpresionRapida: SqlScalar
    BloqueoFormasPago: SqlScalar
    utilizaRecaudoSUIC: SqlScalar
    ImpresoraCaracteresNumero: SqlScalar
    CodigoCentroventa: SqlScalar
    CodigoPuntoVenta: SqlScalar
    NombreCV: SqlScalar
    PresetFullUnicamente: SqlScalar
    TipoAmbiente: SqlScalar
    utilizaFidelizacion: SqlScalar
    utilizaClienteFidelizador: SqlScalar
    utilizaConsultaPremio: SqlScalar
    utilizaEntregaPremio: SqlScalar
    GeneraArchivoVentaPanama: SqlScalar
    utilizaConexionEstacion: SqlScalar
    utilizaZetaDíaAdelantado: SqlScalar
    utilizaCupoIngresaPlaca: SqlScalar
    CantidadCFP: SqlScalar
    CreditoGeneraFactura: SqlScalar
    CapturadorPorCara: SqlScalar
    Codigoarea: SqlScalar
    MaximoVenta: SqlScalar
    SecuencialIdVenta: SqlScalar
    SecuenciaActualFactura: SqlScalar
    UtilizaPreset: SqlScalar
    ManejaFleetTotal: SqlScalar
    FleetTotalManejaCupo: SqlScalar
    FleetTotalVerificaGPS: SqlScalar
    FleetTotalEnviaGPS: SqlScalar
    ValorBolsa: SqlScalar
    NumCaracteresFilaPrecio: SqlScalar
    NumCaracteresFilaDescripcion: SqlScalar
    NumCaracteresFilaCantidad: SqlScalar
    NumCaracteresFilaTotal: SqlScalar
    ValorMaximoCanastilla: SqlScalar
    AplicaSICOM: SqlScalar
    IdTurno: SqlScalar
    FechaZeta: SqlScalar
    Isla: SqlScalar
    Fecha: SqlScalar
    HoraApertura: SqlScalar
    HoraCierre: SqlScalar
    Abierto: SqlScalar
    SincronizoApertura: SqlScalar
    SincronizoCierre: SqlScalar
    NumeroDeTurno: SqlScalar
    SincronizoLecturasIniciales: SqlScalar
    SincronizoLecturasFinales: SqlScalar
    SincronizoTotalOperaciones: SqlScalar
    FechaCierre: SqlScalar
    IdConfiguracionGeneral: SqlScalar
    ManejaZeta: SqlScalar
    ManejaConsola: SqlScalar
    ZetaAutomatica: SqlScalar
    HoraInicioZetaAutomatica: SqlScalar
    HoraFinZetaAutomatica: SqlScalar
    VentasPorIslero: SqlScalar
    ValidaFechaUTC: SqlScalar
    UltimaFechaValidadaUTC: SqlScalar
    IdIsla: SqlScalar
    DescIsla: SqlScalar
    CodigoComprobante: SqlScalar


def license_operations(db: SqlDatabase) -> dict[str, Operation]:
    def station_island() -> int:
        station, _ = request_actor.get()
        try:
            return int(station.split('/')[2])
        except (IndexError, ValueError):
            raise ApiError(403, 'INVALID_STATION', 'Perfil de estación inválido') from None

    def printers():
        return db.read(load_license_query(LicenseQuery.PRINTER_CONFIG), PrinterConfig)

    def rd():
        return db.read(load_license_query(LicenseQuery.RD_CONFIG), RdConfig)

    def medianet():
        return db.read(load_license_query(LicenseQuery.MEDIANET_CONFIG), MedianetConfig)

    def print_sale_points():
        station, _ = request_actor.get()
        try:
            company, center, _ = (int(part) for part in station.split('/'))
        except ValueError:
            raise ApiError(403, 'INVALID_STATION', 'Perfil de estación inválido') from None
        return db.read(load_license_query(LicenseQuery.PRINT_SALE_POINTS), PrintSalePoint,
                       parameters=(company, center))

    def print_sale_point(*, idPuntoVenta: int):
        return db.read(load_license_query(LicenseQuery.PRINT_SALE_POINT), PrintSalePoint, parameters=(idPuntoVenta,))

    def open_shift(*, isla: int | None = None):
        return db.read(load_license_query(LicenseQuery.OPEN_SHIFT), ShiftOpenFlag,
                       parameters=(isla if isla is not None else station_island(),))

    def general_startup():
        return db.read(load_license_query(LicenseQuery.GENERAL_STARTUP), GeneralStartup)

    def shift_startup(*, isla: int | None = None):
        return db.read(load_license_query(LicenseQuery.SHIFT_STARTUP), ShiftStartup,
                       parameters=(isla if isla is not None else station_island(),))

    def pos_startup():
        return db.read(load_license_query(LicenseQuery.POS_STARTUP), PosStartup)

    def capturer_startup():
        return db.read(load_license_query(LicenseQuery.CAPTURER_STARTUP), CapturerStartup)

    def capturer_assignment(*, idIsla: int, numeroCapturador: int):
        return db.read(load_license_query(LicenseQuery.CAPTURER_ASSIGNMENT), CapturerAssignment,
                       parameters=(idIsla, numeroCapturador))

    return {
        "ConsultarAsignacionCapturador": (CapturerAssignmentParameters, capturer_assignment),
        "ListarConfiguracionImpresion": (NoParameters, printers),
        "ListarConfiguracionRD": (NoParameters, rd),
        "ObtenerConfiguracionMedianet": (NoParameters, medianet),
        "ListarPuntosVentaImpresion": (NoParameters, print_sale_points),
        "ListarPuntoVentaImpresion": (PrintSalePointParameters, print_sale_point),
        "ConsultarTurnoAbierto": (OpenShiftParameters, open_shift),
        "ListarConfiguracionOperativaGeneral": (NoParameters, general_startup),
        "ConsultarEstadoTurnoYZeta": (OpenShiftParameters, shift_startup),
        "ListarConfiguracionOperativaPOS": (NoParameters, pos_startup),
        "ListarConfiguracionOperativaCapturador": (NoParameters, capturer_startup),
    }


class EmployeeLogin(StrictModel):
    user: str = Field(min_length=1, max_length=30)
    password: SecretStr = Field(min_length=1, max_length=50)


class EmployeePermissions(BaseModel):
    identificacion: SqlScalar
    Empleado: SqlScalar
    Capturador: SqlScalar
    JornadaZeta: SqlScalar
    turno: SqlScalar
    reimpresion: SqlScalar
    Calibracion: SqlScalar
    ReporteX: SqlScalar
    Codigo: SqlScalar


class EmployeeLoginRow(EmployeePermissions):
    Clave: SecretStr | None


def employee_login_operation(db: SqlDatabase) -> dict[str, Operation]:
    def authenticate(*, user: str, password: SecretStr):
        rows = db.read(load_license_query(LicenseQuery.EMPLOYEE_LOGIN), EmployeeLoginRow,
                       parameters=(user,)) if user.strip().casefold() != "sa" else []
        if len(rows) == 1 and rows[0].Clave is not None and hmac.compare_digest(
            str(rows[0].Clave).encode(), password.get_secret_value().encode()
        ):
            return [rows[0].model_dump(exclude={"Clave"})]
        raise ApiError(403, "EMPLOYEE_LOGIN_REJECTED", "Usuario o contraseña incorrectos")

    return {"ValidarEmpleadoCapturador": (EmployeeLogin, authenticate)}


class EcuadorSettings(StrictModel):
    placaEnvases: str
    prefijoCuantias: str
    prefijoMaquinarias: str


ECUADOR_KEYS = (
    "ECUADOR_PLACA_ENVASES", "ECUADOR_PREFIJO_CUANTIAS", "ECUADOR_PREFIJO_MAQUINARIAS",
)


class EcuadorSetting(StrictModel):
    llave: Literal["ECUADOR_PLACA_ENVASES", "ECUADOR_PREFIJO_CUANTIAS", "ECUADOR_PREFIJO_MAQUINARIAS"]
    valor: str


class ZetaConfig(StrictModel):
    manejaZeta: bool
    zetaAutomatica: bool
    manejaConsola: bool
    horaInicio: str = Field(max_length=32)
    horaFin: str = Field(max_length=32)


class CapturerXml(StrictModel):
    xml: str = Field(min_length=1, max_length=524288)


def license_write_operations(db: SqlDatabase) -> dict[str, Operation]:
    def save_zeta(*, manejaZeta, zetaAutomatica, manejaConsola, horaInicio, horaFin):
        db.write([(load_license_query(LicenseQuery.UPSERT_ZETA_CONFIG),
                   (int(manejaZeta), int(zetaAutomatica), int(manejaConsola), horaInicio, horaFin))])
        return [WriteResult()]

    def save_ecuador(*, placaEnvases: str, prefijoCuantias: str, prefijoMaquinarias: str):
        sql = load_license_query(LicenseQuery.UPSERT_ECUADOR_SETTING)
        fields = zip(ECUADOR_KEYS, (placaEnvases, prefijoCuantias, prefijoMaquinarias), strict=True)
        db.write((sql, (key, value)) for key, value in fields)
        return [WriteResult()]

    def save_ecuador_setting(*, llave: str, valor: str):
        db.write([(load_license_query(LicenseQuery.UPSERT_ECUADOR_SETTING), (llave, valor))])
        return [WriteResult()]

    def save_capturer_xml(*, xml: str):
        db.write([(load_license_query(LicenseQuery.REFRESH_CAPTURER), (xml,))])
        return [WriteResult()]

    return {"GuardarLlaveConfiguracionEcuador": (EcuadorSetting, save_ecuador_setting),
            "GuardarConfiguracionEcuador": (EcuadorSettings, save_ecuador),
            "GuardarConfiguracionZeta": (ZetaConfig, save_zeta),
            "ActualizarConfiguracionCapturadorXml": (CapturerXml, save_capturer_xml)}


class CloudLicense(BaseModel):
    UsuarioLicencia: str
    ContrasenaLicencia: str


class CloudLicenseIdentity(BaseModel):
    IdCompania: int
    IdCentroVenta: int
    CodigoIsla: int
    UsuarioLicencia: str
    ContrasenaLicencia: str


def authenticate_cloud_license(db: SqlDatabase, company: int, user: str,
                               password: str) -> str:
    rows = db.read(
        "SELECT IdCompania, IdCentroVenta, CodigoIsla, UsuarioLicencia, "
        "ContrasenaLicencia FROM dbo.ConfiguracionInicial "
        "WHERE IdCompania = ? AND UsuarioLicencia = ?;",
        CloudLicenseIdentity,
        parameters=(company, user),
    )
    matches = [row for row in rows if hmac.compare_digest(row.ContrasenaLicencia, password)]
    if len(matches) != 1:
        raise ApiError(401, "LICENSE_LOGIN_REJECTED", "Credenciales de licenciamiento inválidas")
    row = matches[0]
    return f"{row.IdCompania}/{row.IdCentroVenta}/{row.CodigoIsla}"


def load_cloud_license(db: SqlDatabase, station: str) -> tuple[int, CloudLicense]:
    try:
        company, center, island = (int(part) for part in station.split("/"))
    except ValueError:
        raise ApiError(403, "INVALID_STATION", "Perfil de estación inválido") from None
    rows = db.read(load_license_query(LicenseQuery.CLOUD_LICENSE), CloudLicense,
                   parameters=(company, center, island))
    if len(rows) != 1 or not rows[0].UsuarioLicencia.strip() or not rows[0].ContrasenaLicencia:
        raise ApiError(409, "CLOUD_LICENSE_UNAVAILABLE", "Licencia Cloud no disponible para la estación")
    return company, rows[0]


def cloud_license_operation(db: SqlDatabase) -> dict[str, Operation]:
    def get_license():
        station, _ = request_actor.get()
        _, license = load_cloud_license(db, station)
        return [license]

    return {"ObtenerLicenciaCloudCapturador": (NoParameters, get_license)}


class ShiftEmployeeProof(EmployeeLogin):
    idTurno: int = Field(gt=0, le=2147483647)


class ShiftEmployeeRow(BaseModel):
    Identificacion: str
    ClaveTurno: SecretStr | None


class ShiftEmployeeValidation(BaseModel):
    valido: bool


def shift_employee_operation(db: SqlDatabase) -> dict[str, Operation]:
    def check(*, idTurno: int, user: str, password: SecretStr):
        station, _ = request_actor.get()
        try:
            _, _, island = (int(part) for part in station.split("/"))
        except ValueError:
            raise ApiError(403, "INVALID_STATION", "Perfil de estación inválido") from None
        rows = db.read(load_license_query(LicenseQuery.SHIFT_EMPLOYEE), ShiftEmployeeRow,
                       parameters=(idTurno, island, user))
        valid = len(rows) == 1 and rows[0].Identificacion == user and rows[0].ClaveTurno is not None and hmac.compare_digest(
            str(rows[0].ClaveTurno).encode(), password.get_secret_value().encode())
        return [ShiftEmployeeValidation(valido=valid)]

    return {"ValidarClaveEmpleadoTurno": (ShiftEmployeeProof, check)}


class StartupTerminal(BaseModel):
    IdConfiguracion: SqlScalar
    MID: SqlScalar
    TID: SqlScalar
    TIC: SqlScalar


class StartupShiftIdentity(BaseModel):
    IdTurno: SqlScalar
    Identificacion: SqlScalar
    EmpleadoTurno: SqlScalar
    CodigoEmpleado: SqlScalar
    EmpleadoJornadaZeta: SqlScalar
    XMLApertura: str | None


def startup_identity_operations(db: SqlDatabase) -> dict[str, Operation]:
    def station_ids():
        station, _ = request_actor.get()
        try:
            company, center, island = (int(part) for part in station.split('/'))
        except ValueError:
            raise ApiError(403, "INVALID_STATION", "Perfil de estación inválido") from None
        return company, center, island

    def terminal():
        company, center, island = station_ids()
        return db.read(load_license_query(LicenseQuery.STARTUP_TERMINAL), StartupTerminal,
                       parameters=(company, island, center))

    def shift():
        company, center, island = station_ids()
        rows = db.read(load_license_query(LicenseQuery.STARTUP_SHIFT_IDENTITY), StartupShiftIdentity,
                       parameters=(island, company, center))
        for row in rows:
            if not row.XMLApertura:
                continue
            try:
                source = fromstring(row.XMLApertura)
                output = Element('LECTURA')
                SubElement(output, 'TIPO').text = source.findtext('.//TIPO', '')
                for reading in source.findall('.//LECTURAS'):
                    target = SubElement(output, 'LECTURAS')
                    for tag in ('CARA', 'MANGUERA', 'CANTIDAD', 'VALORNETO', 'PRECIO_UNI'):
                        SubElement(target, tag).text = reading.findtext(tag, '')
                row.XMLApertura = tostring(output, encoding='unicode')
            except (SyntaxError, ValueError):
                raise ApiError(502, 'SHIFT_READINGS_INVALID', 'Lecturas de apertura inválidas') from None
        return rows

    return {"ConsultarTerminalArranquePOS": (NoParameters, terminal),
            "ConsultarIdentidadTurnoArranque": (NoParameters, shift)}


CLOUD_REFRESH_KEYS = frozenset({
    'API_MESSAGES',
    'API_PANTERA_PAGO_PANTERA_PAGO',
    'BLOQUEAR_MODIFICACION_CONDUCTOR_CUANDO_FAC_CONDUCTOR',
    'CANTIDAD_MAX_CAMBIOFP_MULTIPLE',
    'CENTROVENTAFIDELIZACION',
    'CONFIGURACION_CUPONES_PROMOCIONES_MENSAJE',
    'CREDITOS_CONTINGENCIA_CANAL',
    'CREDITOS_CONTINGENCIA_CORREO_DESTINO',
    'CREDITOS_CONTINGENCIA_CRITERIO_ACTIVACION',
    'CREDITOS_CONTINGENCIA_ID_TEMPLATE_WHATSAPP',
    'CREDITOS_CONTINGENCIA_OTP',
    'CREDITOS_CONTINGENCIA_TIMEOUT',
    'CREDITOS_CONTINGENCIA_WHATSAPP_DESTINO',
    'CREDITOS_CONTINGENCIA_WHATSAPP_ORIGEN',
    'DESHABILITAR_CAMBIO_FP_MULTIPLE',
    'DESHABILITAR_CONVERSION_FAC_CONS_FINAL',
    'EDS_BLOQUEAR_MODIFICACION_CLIENTE',
    'EDS_NO_FACTURAR_AUTOMATICAMENTE_VENTAS_CONSUMIDOR_FINAL',
    'EDS_VALIDA_TIPO_VEHICULO',
    'HABILITAR_CAMBIO_MODO_CARAS',
    'IMPRIMIR_ERRORES_AL_LEER_CHIP',
    'IMPRIMIR_SALDO_INVENTARIO_ARTICULO',
    'INVENTARIO_PERMITE_EXISTENCIA_NEGATIVA',
    'MANEJA_DESCUENTO_SOLO_POR_REVOLUTION',
    'NO_UTILIZA_RANGO_HORARIO_PARA_CAMBIO_DE_Z',
    'NUEVA_VALIDACION_PREPAGO',
    'OMITIR_VALIDACION_AUTOMATICA_CLIENTEPLACA_GAS',
    'PASS_PANTERA_PAGO',
    'PERMITE_CONSIGNACION_NEGATIVO',
    'PREGUNTAR_SI_ACUMULA_PUNTOS',
    'UID_PANTERA_PAGO',
    'USER_UTILIZA_PANTERA_PAGO',
    'UTILIZA_CREDITOS_CONTINGENCIA',
    'UTILIZA_GASTOS',
    'UTILIZA_PANTERA_PAGO',
})


class StartupSetting(StrictModel):
    key: str = Field(max_length=200)
    value: str = Field(max_length=16000)


class StartupPayment(StrictModel):
    code: str = Field(max_length=32)
    electronic: str = Field(max_length=64)


class CloudRefresh(StrictModel):
    heads: list[str] = Field(min_length=1, max_length=32)
    zeta: ZetaConfig
    settings: list[StartupSetting] = Field(max_length=100)
    vehicles: VehicleTypeReplace | None = None
    expenses: ExpenseTypeReplace | None = None
    payments: list[StartupPayment] = Field(max_length=250)
    message: str = Field(max_length=8000)


def cloud_refresh_operation(db: SqlDatabase) -> dict[str, Operation]:
    def refresh(*, heads, zeta, settings, vehicles, expenses, payments, message):
        station, _ = request_actor.get()
        if station != '900716/10370/1':
            raise ApiError(403, 'STATION_MISMATCH', 'Estación no autorizada para el piloto')
        keys = [item['key'] for item in settings]
        if len(keys) != len(set(keys)) or not CLOUD_REFRESH_KEYS.issuperset(keys):
            raise ApiError(400, 'INVALID_PARAMETERS', 'Configuración Cloud no permitida')
        if expenses and any(item['idcompania'] != 900716 for item in expenses['items']):
            raise ApiError(403, 'STATION_MISMATCH', 'Compañía no autorizada')

        xml = Element('Items')
        for item in settings:
            # La respuesta Cloud puede traer JSON codificado como entidades HTML.
            # XML vuelve a escapar el atributo correctamente y SQL recibe el
            # valor original (por ejemplo, JSON con comillas reales).
            SubElement(xml, 'Item', Llave=item['key'], Valor=unescape(item['value']))
        statements = [
            (load_license_query(LicenseQuery.REFRESH_DEMO_GUARD), ()),
            (load_license_query(LicenseQuery.UPSERT_ZETA_CONFIG), (
                int(zeta['manejaZeta']), int(zeta['zetaAutomatica']), int(zeta['manejaConsola']),
                zeta['horaInicio'], zeta['horaFin'],
            )),
            (load_license_query(LicenseQuery.REFRESH_CAPTURER), (tostring(xml, encoding='unicode'),)),
        ]
        if vehicles is not None:
            statements.append((load_query(ArticleQuery.DELETE_VEHICLE_TYPES), ()))
            statements.extend((load_query(ArticleQuery.INSERT_VEHICLE_TYPE),
                               (item['idtipovehiculo'], item['tipovehiculo'])) for item in vehicles['items'])
        if expenses is not None:
            statements.append((load_query(ArticleQuery.DELETE_EXPENSE_TYPES), ()))
            statements.extend((load_query(ArticleQuery.INSERT_EXPENSE_TYPE), (
                item['idgastotipo'], item['idcompania'], item['gastotipo'], item['contabilidadcuenta'],
                item['estado'], item['fechacreacion'], item['fechamodificacion'], item['fechaultimomovimiento'],
            )) for item in expenses['items'])
        first_payment = {}
        for item in payments:
            first_payment.setdefault(item['code'], item['electronic'])
        statements.extend((load_license_query(LicenseQuery.REFRESH_PAYMENT), (value, code))
                          for code, value in first_payment.items())
        statements.append((load_license_query(LicenseQuery.REFRESH_INITIAL), (message,)))
        db.write(statements)
        articles = ArticleRepository(db)
        result_sets = {
            "VALIDATE_TIPO_ZETA": [WriteResult()],
            "ACTUALIZAR_CONFIG_CAPTURADOR": [WriteResult()],
            "GET_CONFIG_CAPTURADOR": db.read(
                load_license_query(LicenseQuery.CAPTURER_STARTUP), CapturerStartup,
            ),
        }
        if vehicles is not None:
            result_sets.update({
                "DELETE_TIPO_VEHICULO": [WriteResult()],
                "INSERT_VEHICULOS": [WriteResult()],
                "GET_TIPO_VEHICULO": articles.list_vehicle_types(),
            })
        if expenses is not None:
            result_sets.update({
                "DELETE_TIPO_GASTO": [WriteResult()],
                "INSERT_TIPO_GASTO": [WriteResult()],
                "GET_GASTO_TIPO": articles.list_expense_types(),
            })
        if payments:
            result_sets["UPDATE_FORMAS_PAGO"] = [WriteResult()]
        result_sets.update({
            "UPDATE_CONFIGURACION_INICIAL": [WriteResult()],
            "GET_CONFIG_GENERAL": db.read(
                load_license_query(LicenseQuery.GENERAL_STARTUP), GeneralStartup,
            ),
        })
        if heads != list(result_sets):
            raise ApiError(400, 'INVALID_PARAMETERS', 'Heads de lote inválidos')
        return [{"resultSets": result_sets}]

    return {'ActualizarArranqueCloud': (CloudRefresh, refresh)}


class StartupBatch(StrictModel):
    heads: list[str] = Field(min_length=1, max_length=32)
    idPuntoVenta: int = Field(ge=0)


def startup_batch_operation(db: SqlDatabase) -> dict[str, Operation]:
    def batch(*, heads, idPuntoVenta):
        station, _ = request_actor.get()
        try:
            island = int(station.rsplit('/', 1)[1])
        except (ValueError, IndexError):
            raise ApiError(403, 'INVALID_STATION', 'Perfil de estación inválido') from None
        routes = {
            'CONFIG_POS': ('ListarConfiguracionOperativaPOS', {}),
            'CONFIG_CAPTURADOR': ('ListarConfiguracionOperativaCapturador', {}),
            'CONFIG_PRINT': ('ListarConfiguracionImpresion', {}),
            'CONFIG_RD': ('ListarConfiguracionRD', {}),
            'CONFIG_MEDIANET': ('ObtenerConfiguracionMedianet', {}),
            'PUNTO_VENTA_IMPRESION': ('ListarPuntoVentaImpresion', {'idPuntoVenta': idPuntoVenta}),
            'TURNO_ABIERTO': ('ConsultarTurnoAbierto', {'isla': island}),
            'GET_TURNO_TURNO_ZETA': ('ConsultarEstadoTurnoYZeta', {'isla': island}),
            'SUBSIDIO_ECUADOR': ('ListarSubsidiosEcuador', {}),
            'COMBUSTIBLE': ('ListarCombustibles', {}),
            'MANGUERA_TANQUE': ('ListarManguerasTanques', {}),
            'CONFIGURACION_REDONDEO': ('ListarConfiguracionRedondeo', {}),
            'CAMBIO_FORMA_DE_PAGO_POS': ('ListarCambiosFormaPagoPOS', {}),
            'FORMA_PAGO_POS': ('ListarFormasPagoPOS', {}),
            'COMBUSTIBLE_CARA': ('ListarCombustiblesPorCara', {}),
            'TIPO_VEHICULO': ('ListarTiposVehiculo', {}),
            'GASTO_TIPO': ('ListarTiposGasto', {}),
        }
        if any(head not in routes for head in heads):
            raise ApiError(400, 'INVALID_PARAMETERS', 'Head de arranque no autorizado')
        operations = {
            **license_operations(db),
            **article_operations(ArticleRepository(db)),
        }
        result_sets = {}
        for head in heads:
            operation, parameters = routes[head]
            schema, handler = operations[operation]
            values = schema.model_validate(parameters).model_dump()
            result = handler(**values)
            result_sets[head] = result if isinstance(result, list) else [result]
        return [{'resultSets': result_sets}]

    return {'EjecutarLoteConfiguracionInicial': (StartupBatch, batch)}


class InitialEnvironment(StrictModel):
    tipoAmbiente: int = Field(ge=-2147483648, le=2147483647)
    codeIsla: str = Field(max_length=32)


def initial_environment_operation(db: SqlDatabase) -> dict[str, Operation]:
    def update(*, tipoAmbiente: int, codeIsla: str):
        station, _ = request_actor.get()
        if station != '900716/10370/1' or codeIsla != station.rsplit('/', 1)[1]:
            raise ApiError(403, 'STATION_MISMATCH', 'Estación no autorizada para el piloto')
        count = db.write([
            (load_license_query(LicenseQuery.REFRESH_DEMO_GUARD), ()),
            (load_license_query(LicenseQuery.UPDATE_INITIAL_ENVIRONMENT), (tipoAmbiente, codeIsla)),
        ], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def capturer(*, llave: str, valor: str):
        return scoped_write(LicenseQuery.UPDATE_CAPTURER_SETTING, (valor, llave))

    def initial(*, utilizaFidelizacion: int, mensaje: str):
        return scoped_write(LicenseQuery.UPDATE_INITIAL_SETTINGS, (utilizaFidelizacion, mensaje))

    def scoped_write(query, parameters):
        station, _ = request_actor.get()
        if station != '900716/10370/1':
            raise ApiError(403, 'STATION_MISMATCH', 'Estación no autorizada para el piloto')
        count = db.write([(load_license_query(LicenseQuery.REFRESH_DEMO_GUARD), ()),
                          (load_license_query(query), parameters)], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def electronic_payment(*, code: str, electronic: str):
        count = db.write([
            (load_license_query(LicenseQuery.REFRESH_DEMO_GUARD), ()),
            (load_license_query(LicenseQuery.REFRESH_PAYMENT), (electronic, code)),
        ], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def demo_insert(query, parameters):
        count = db.write([
            (load_license_query(LicenseQuery.REFRESH_DEMO_GUARD), ()),
            (load_license_query(query), parameters),
        ], count_rows=True)
        return [SqlAffectedRows(affectedRows=count)]

    def insert_capturer(*, llave, valor):
        station, _ = request_actor.get()
        try:
            company, center, island = (int(part) for part in station.split('/'))
        except ValueError:
            raise ApiError(403, 'INVALID_STATION', 'Perfil de estación inválido') from None
        return demo_insert(LicenseQuery.INSERT_CAPTURER_SETTING, (company, center, island, llave, valor))

    def upsert_capturer(*, llave, valor):
        return demo_insert(
            LicenseQuery.UPSERT_CAPTURER_SETTING,
            (llave, valor, llave, llave, valor),
        )

    def insert_certifier(*, llave, valor):
        return demo_insert(LicenseQuery.INSERT_CERTIFIER_SETTING, (llave, valor))

    def delete_certifier(*, llave):
        return demo_insert(LicenseQuery.DELETE_CERTIFIER_SETTING, (llave,))

    def insert_loyalty_type(*, idClienteFidelizado, clienteFidelizado):
        return demo_insert(LicenseQuery.INSERT_LOYALTY_TYPE, (idClienteFidelizado, clienteFidelizado))

    def list_loyalty_types():
        return db.read(load_license_query(LicenseQuery.LIST_LOYALTY_TYPES), LoyaltyTypeRow)

    return {'EliminarCertificadorGuatemala': (CertifierKey, delete_certifier),
            'InsertarLlaveConfiguracionCapturador': (CapturerSettingUpdate, insert_capturer),
            'InsertarCertificadorGuatemala': (CertifierSetting, insert_certifier),
            'InsertarTipoClienteFidelizado': (LoyaltyType, insert_loyalty_type),
            'ListarTiposClienteFidelizado': (NoParameters, list_loyalty_types),
            'ActualizarFormaPagoFacturaElectronica': (StartupPayment, electronic_payment),
            'ActualizarAmbienteConfiguracionInicial': (InitialEnvironment, update),
            'ActualizarLlaveConfiguracionCapturador': (CapturerSettingUpdate, capturer),
            'GuardarLlaveConfiguracionCapturador': (CapturerSettingUpdate, upsert_capturer),
            'ActualizarConfiguracionInicial': (InitialSettingsUpdate, initial)}


class CertifierKey(StrictModel):
    llave: Literal["DATOS_CERTIFICADOR_GTM"]


class CertifierSetting(CertifierKey):
    valor: str


class LoyaltyType(StrictModel):
    idClienteFidelizado: int = Field(ge=-2147483648, le=2147483647)
    clienteFidelizado: str


class LoyaltyTypeRow(BaseModel):
    IdClienteFidelizado: int
    ClienteFidelizado: str | None


class CapturerSettingUpdate(StrictModel):
    llave: str = Field(max_length=200)
    valor: str = Field(max_length=16000)


class InitialSettingsUpdate(StrictModel):
    utilizaFidelizacion: int = Field(ge=-2147483648, le=2147483647)
    mensaje: str = Field(max_length=16000)
