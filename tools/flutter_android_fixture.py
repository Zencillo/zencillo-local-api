"""Private fixture IO for the authorized, read-only Android pilot emulator."""
from pathlib import Path
import subprocess
import time

ADB = Path("C:/Users/ZSDeveloper15/AppData/Local/Android/sdk/platform-tools/adb.exe")
APK = Path("C:/dev/capturador_mobile/build/app/outputs/flutter-apk/app-pos-debug.apk")
DEVICE = "emulator-5570"
PACKAGE = "com.zencillo.zs_capturadorandroid"
FOLDER = "files/zencillo-pilot"
FILES = ("ca.pem", "origin.txt", "expected.json", "bootstrap.secret", "restart.request",
         "offline.ready", "offline.checked", "restart.ready", "pilot.passed", "pilot.failed",
         "group", "group.ready", "group.start")


def adb(*args, data=None, check=True):
    return subprocess.run([str(ADB), "-s", DEVICE, *args], input=data,
               check=check, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=75)


def inside(command, **kw):
    return adb("shell", "-T", f"run-as {PACKAGE} sh -c '{command}'", **kw)


def send(name, data):
    if name not in FILES:
        raise ValueError("Unexpected pilot fixture.")
    inside(f"cat > {FOLDER}/{name}", data=data)


def exists(name):
    if name not in FILES:
        raise ValueError("Unexpected pilot fixture.")
    return inside(f"test -f {FOLDER}/{name}", check=False).returncode == 0


def prepare(folder, secret):
    adb("install", "-r", str(APK))
    inside(f"mkdir -p {FOLDER}")
    for name in FILES:
        inside(f"rm -f {FOLDER}/{name}")
    for name in ("ca.pem", "origin.txt", "expected.json"):
        send(name, (folder / name).read_bytes())
    send("bootstrap.secret", secret.encode())


def wait_for_certificate_clock(issued_at):
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        result = subprocess.check_output(
            [str(ADB), "-s", DEVICE, "shell", "date", "+%s"],
            timeout=10, text=True,
        )
        if int(result.strip()) >= issued_at:
            return
        time.sleep(2)
    raise RuntimeError("El reloj del emulador aún está antes de la vigencia del certificado.")


def launch():
    adb("shell", "am", "force-stop", PACKAGE)
    adb("shell", "am", "start", "-n", f"{PACKAGE}/.MainActivity")


def failure():
    result = subprocess.run(
        [str(ADB), "-s", DEVICE, "shell", "-T", f"run-as {PACKAGE} cat {FOLDER}/pilot.failed"],
        capture_output=True, timeout=5, text=True,
    )
    stage = result.stdout.strip()
    return stage if result.returncode == 0 and stage.isascii() and stage.replace("_", "").isalnum() else None


def clean():
    for name in FILES:
        inside(f"rm -f {FOLDER}/{name}", check=False)
    inside(f"rmdir {FOLDER}", check=False)
