"""Durable, fail-closed admission control for the station payment operation."""
import csv
import os
import re
import sqlite3
import stat
import subprocess
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.errors import ApiError


UUID4 = r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
REFERENCE = r"^[A-Za-z0-9_.-]{1,32}$"


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def _private_directory(path: Path):
    path.mkdir(mode=0o700)
    if os.name == "nt":
        system32 = Path(os.environ["SystemRoot"]) / "System32"
        identity = subprocess.check_output([system32 / "whoami.exe", "/user", "/fo", "csv", "/nh"], text=True)
        sid = next(csv.reader(identity.splitlines()))[1]
        subprocess.run(
            [system32 / "icacls.exe", str(path), "/inheritance:r", "/grant:r",
             f"*{sid}:(OI)(CI)F", "*S-1-5-18:(OI)(CI)F", "*S-1-5-32-544:(OI)(CI)F"],
            check=True, capture_output=True,
        )


class PaymentAttempts:
    def __init__(self, directory: Path, *, initialize: bool = False):
        self.path = directory.absolute() / "attempts.sqlite3"
        self.owner = str(uuid4())
        self.lock_path = self.path.parent / "service.lock"
        if initialize:
            _private_directory(self.path.parent)
            self.lock_path.write_bytes(b"\0")
            with closing(sqlite3.connect(self.path)) as db, db:
                db.executescript("""
                    CREATE TABLE attempts (
                        id TEXT PRIMARY KEY NOT NULL, station TEXT NOT NULL, device TEXT NOT NULL,
                        invoice INTEGER NOT NULL, fingerprint TEXT NOT NULL, reference TEXT,
                        state TEXT NOT NULL CHECK(state IN ('PENDING','PROCESSING','APPLIED','FAILED','UNCERTAIN')),
                        owner TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                        result TEXT, evidence TEXT
                    );
                    CREATE UNIQUE INDEX active_invoice ON attempts(station, invoice)
                      WHERE state IN ('PENDING','PROCESSING','UNCERTAIN');
                """)
        if initialize and os.name != "nt":
            self.path.chmod(0o600)
        for path in (self.path.parent, self.path, self.lock_path):
            info = path.lstat()
            if path.is_symlink() or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise ValueError("Se rechaza un registro de intentos redirigido.")
        if os.name != "nt" and self.path.parent.stat().st_mode & 0o077:
            raise ValueError("El directorio del registro de intentos debe ser privado.")

    @contextmanager
    def service_lock(self):
        """The server and the offline reconciler cannot use the ledger together."""
        with self.lock_path.open("r+b") as lock:
            try:
                if os.name == "nt":
                    from msvcrt import LK_NBLCK, locking
                    locking(lock.fileno(), LK_NBLCK, 1)
                else:
                    from fcntl import LOCK_EX, LOCK_NB, flock
                    flock(lock.fileno(), LOCK_EX | LOCK_NB)
            except OSError:
                raise RuntimeError("El registro de intentos está en uso. Detenga el servidor de pagos.") from None
            yield

    def connection(self):
        # Opening read/write without create is essential if a ledger is lost.
        db = sqlite3.connect(self.path.as_uri() + "?mode=rw", uri=True, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        return db

    def recover(self):
        """Called exclusively on startup. An interrupted write is never reclaimed."""
        with closing(self.connection()) as db, db:
            db.execute(
                """UPDATE attempts SET state='UNCERTAIN',result='WRITE_OUTCOME_UNKNOWN',updated_at=?
                   WHERE state IN ('PENDING','PROCESSING')""", (timestamp(),),
            )

    def public_state(self, row):
        state = row["state"]
        if state == "PROCESSING" and row["owner"] != self.owner:
            return "UNCERTAIN"
        return state

    def claim(self, operation_id, station, device, invoice, fingerprint, reference):
        with closing(self.connection()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT * FROM attempts WHERE id=?", (operation_id,)).fetchone()
            if old is not None:
                if (old["station"], old["device"], old["fingerprint"]) != (station, device, fingerprint):
                    raise ApiError(409, "PAYMENT_ATTEMPT_CONFLICT", "El intento no coincide con la solicitud original")
                return self.public_state(old)
            active = db.execute(
                """SELECT 1 FROM attempts WHERE station=? AND invoice=?
                   AND state IN ('PENDING','PROCESSING','UNCERTAIN')""", (station, invoice),
            ).fetchone()
            if active is not None:
                raise ApiError(409, "PAYMENT_ATTEMPT_ACTIVE", "La factura tiene un intento pendiente de conciliación")
            now = timestamp()
            db.execute(
                """INSERT INTO attempts (id,station,device,invoice,fingerprint,reference,state,owner,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,'PENDING',?,?,?)""",
                (operation_id, station, device, invoice, fingerprint, reference, self.owner, now, now),
            )
            db.execute("UPDATE attempts SET state='PROCESSING' WHERE id=?", (operation_id,))
        return None

    def finish(self, operation_id, state, result):
        with closing(self.connection()) as db, db:
            changed = db.execute(
                """UPDATE attempts SET state=?, result=?, updated_at=?
                   WHERE id=? AND state='PROCESSING' AND owner=?""",
                (state, result, timestamp(), operation_id, self.owner),
            ).rowcount
            if changed != 1:
                raise sqlite3.OperationalError("La reserva ya no le pertenece al ejecutor.")

    def status(self, operation_id, station, device):
        with closing(self.connection()) as db:
            row = db.execute("SELECT * FROM attempts WHERE id=? AND station=? AND device=?",
                             (operation_id, station, device)).fetchone()
            if not row:
                raise ApiError(404, "PAYMENT_ATTEMPT_NOT_FOUND", "Intento de pago no encontrado")
            return self.public_state(row), row["result"]

    def reconcile(self, operation_id, station, state, evidence):
        """Used offline by the station operator with independent evidence."""
        if not re.fullmatch(UUID4, operation_id) or state not in {"APPLIED", "FAILED"}:
            raise ValueError("Intento o estado de resolución inválido.")
        if not re.fullmatch(REFERENCE, evidence) or sum(ch.isdigit() for ch in evidence) >= 12:
            raise ValueError("Use únicamente un código de evidencia de soporte.")
        with self.service_lock(), closing(self.connection()) as db, db:
            changed = db.execute(
                """UPDATE attempts SET state=?, result='RECONCILED', evidence=?, updated_at=?
                   WHERE id=? AND station=? AND state IN ('PROCESSING','PENDING','UNCERTAIN')""",
                (state, evidence, timestamp(), operation_id, station),
            ).rowcount
            if changed != 1:
                raise ValueError("El intento no está pendiente de conciliación en esta estación.")
