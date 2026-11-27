"""Windows Credential Manager for the fixed SQL DEMO diagnostics."""
import argparse
from getpass import GetPassWarning, getpass
import warnings

from app.core.windows_credentials import read as read_target, save as save_target

TARGET = "ZencilloLocalApi/SQL-DEMO/10.1.10.15:1433/ZencilloAutomatizacion"
def read():
    return read_target(target=TARGET)


def save(user, password):
    save_target(user, password, target=TARGET)


def require():
    try:
        found = read()
    except OSError as exc:
        raise SystemExit(str(exc)) from None
    if not found or not all(found):
        raise SystemExit("Falta la credencial DEMO. Ejecuta una vez: python -m tools.demo_credentials --setup")
    return found


def add_tls_options(parser):
    parser.add_argument("--allow-unverified-demo", action="store_true",
                        help="Ofrece la excepciÃ³n TLS exclusivamente para DEMO")
    parser.add_argument("--confirm-demo-exception", action="store_true",
                        help="Autoriza explÃ­citamente esa excepciÃ³n en esta ejecuciÃ³n sin prompt")


def accept_exception(args):
    if not args.allow_unverified_demo:
        return False
    print("AVISO DEMO: conexiÃ³n cifrada sin validar la identidad del servidor.")
    if args.confirm_demo_exception:
        return True
    try:
        return input("Para autorizar escribe DEMO SIN VALIDAR: ").strip() == "DEMO SIN VALIDAR"
    except EOFError:
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--status", action="store_true")
    group.add_argument("--status-bool", action="store_true")
    group.add_argument("--setup", action="store_true")
    group.add_argument("--rotate", action="store_true")
    args = parser.parse_args()
    try:
        found = read()
        if args.status_bool:
            available = bool(found and all(found))
            print(str(available).lower())
            return 0 if available else 1
        if args.status:
            print("Credencial DEMO disponible." if found and all(found) else "Sin credencial DEMO.")
            return 0 if found and all(found) else 1
        if found and not args.rotate:
            print("Credencial DEMO existente conservada.")
            return 0
        user = input("Usuario SQL DEMO [sa]: ").strip() or "sa"
        with warnings.catch_warnings():
            warnings.simplefilter("error", GetPassWarning)
            try:
                password = getpass("ContraseÃ±a SQL DEMO (entrada oculta, una vez): ")
            except GetPassWarning:
                raise SystemExit("La consola no garantiza la entrada oculta.") from None
        save(user, password)
        if read() != (user, password):
            raise OSError("La credencial escrita no pudo verificarse en este perfil.")
        print("Credencial DEMO guardada y verificada en Windows Credential Manager.")
        return 0
    except (OSError, ValueError) as exc:
        raise SystemExit(str(exc)) from None


if __name__ == "__main__":
    raise SystemExit(main())
