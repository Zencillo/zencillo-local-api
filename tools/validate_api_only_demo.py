from contextlib import closing
from datetime import datetime
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess

import pyodbc

from app.config import Device, Settings
from app.core.database import odbc_failure
from app.core.security import hash_secret
from app.main import create_app, registered_operations
from app.modules.article.repository import ArticleQuery, load_query
from app.modules.shift.operations import ShiftQuery, load_shift_query
from tools.demo_config import HOST, PORT, DATABASE, connection_string, require
from tools.run_flutter_windows_pilot import TestServer, FLUTTER
from tools.run_phase13_demo import read_rows
from tools.validate_config_plate_demo import GuardedCommit


def rows(cursor, sql, *args):
    cursor.execute(sql, *args)
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def assert_reversible(cursor, tables):
    identity = cursor.execute('''SELECT DB_NAME(),local_net_address,local_tcp_port,encrypt_option
        FROM sys.dm_exec_connections WHERE session_id=@@SPID''').fetchone()
    assert tuple(identity) == (DATABASE, HOST, PORT, 'TRUE')
    for table in tables:
        metadata = cursor.execute('''SELECT temporal_type,is_tracked_by_cdc,is_replicated,
          (SELECT COUNT(*) FROM sys.columns WHERE object_id=t.object_id AND is_identity=1),
          (SELECT COUNT(*) FROM sys.triggers WHERE parent_id=t.object_id AND is_disabled=0),
          (SELECT COUNT(*) FROM sys.change_tracking_tables WHERE object_id=t.object_id),
          (SELECT COUNT(*) FROM sys.foreign_keys WHERE is_disabled=0 AND
            (parent_object_id=t.object_id OR referenced_object_id=t.object_id))
          FROM sys.tables t WHERE t.object_id=OBJECT_ID(?)''', table).fetchone()
        assert tuple(metadata) == (0, False, False, 0, 0, 0, 0)


def validate():
    profile = Path('.venv/local-api-debug').resolve()
    args = require()
    try:
        with closing(pyodbc.connect(connection_string(*args), timeout=5)):
            verify = True
    except pyodbc.Error as exc:
        if odbc_failure(exc)[1] != 'certificate_trust':
            raise
        verify = False
    sql = connection_string(*args, verify=verify)
    print(f'ODBC_DEMO_CERT_EXCEPTION={not verify}', flush=True)
    fixture = 'LAB-' + secrets.token_hex(8)
    password = secrets.token_urlsafe(18)
    device_secret = secrets.token_urlsafe(32)
    writes = {
        'ReemplazarTiposVehiculo': ('tipo_vehiculo', {'idtipovehiculo': -2147483000, 'tipovehiculo': "LAB O'Brien"}),
        'ReemplazarTiposGasto': ('gasto_tipo', dict(
            idgastotipo=-2147483000, idcompania=1, gastotipo="LAB O'Brien", contabilidadcuenta='0007', estado=1,
            fechacreacion='2026-11-26T09:30:00', fechamodificacion='2026-11-26T09:30:00',
            fechaultimomovimiento='2026-11-26T09:30:00',
        )),
    }
    seen = set()

    def check_transaction(cursor):
        for operation, (table, fields) in writes.items():
            snapshot = rows(cursor, f'SELECT * FROM dbo.{table}')
            if len(snapshot) != 1 or snapshot[0].get(next(iter(fields))) != -2147483000:
                continue
            actual = {key: snapshot[0][key] for key in fields}
            actual = {key: value.isoformat() if isinstance(value, datetime) else value for key, value in actual.items()}
            assert actual == fields
            seen.add(operation)

    def connect(connection, **kwargs):
        raw = pyodbc.connect(connection, **kwargs)
        return raw if kwargs['autocommit'] else GuardedCommit(raw, check_transaction, reject=True)

    with closing(pyodbc.connect(sql, autocommit=True, timeout=6)) as cn, closing(cn.cursor()) as cursor:
        assert_reversible(cursor, ('dbo.PermisosEmpleado', 'dbo.tipo_vehiculo', 'dbo.gasto_tipo'))
        vehicle_query = 'SELECT idtipovehiculo, tipovehiculo FROM dbo.tipo_vehiculo'
        vehicles = rows(cursor, vehicle_query)
        assert len(vehicles) == 19
        assert all(-2147483000 not in [row[0] for row in cursor.execute(f'SELECT {next(iter(fields))} FROM dbo.{table}')]
                   for table, fields in writes.values())
        baselines = {table: sorted(map(str, rows(cursor, f'SELECT * FROM dbo.{table}'))) for table, _ in writes.values()}
        functional = [
            {'operation': 'ConsultarExisteTurnoAbiertoIsla', 'parameters': {'isla': 1},
             'rows': read_rows(cursor.execute(load_shift_query(ShiftQuery.ISLAND_HAS_OPEN_SHIFT), 1))[1]},
            {'operation': 'ListarCombustiblesPorCara', 'parameters': {},
             'rows': read_rows(cursor.execute(load_query(ArticleQuery.FUELS_BY_FACE)))[1]},
        ]
        sale_models = FLUTTER / 'packages/pos_api/lib/features/sale/models'
        clients_source = (sale_models / 'predespacho_cliente_bd.dart').read_text(encoding='utf8')
        pending_source = (sale_models / 'predespacho_pendiente_bd.dart').read_text(encoding='utf8')
        dispatch_sql = clients_source.split('static String readQuery(', 1)[1].split("return '''", 2)[2].split("'''", 1)[0]
        pending_sql = pending_source.split('static String readQuery(', 1)[1].split("return '''", 1)[1].split("'''", 1)[0]
        pending_sql = pending_sql.replace('$filtroIdTurno', 'CheckVentasEstacion.IdTurno = ?')
        comparisons = [
            ('ListarPredespachosClientes', {}, dispatch_sql, ()),
            ('ListarPredespachosPendientes', {'idTurno': 4494, 'cara': None}, pending_sql, (4494,)),
            ('ListarPredespachosPendientes', {'idTurno': 4494, 'cara': 4},
             pending_sql.replace('ORDER BY IdVentaEstacion', 'AND Venta.CodigoCara = ? ORDER BY IdVentaEstacion'), (4494, 4)),
        ]
        for operation, params, query, binds in comparisons:
            try:
                expected = read_rows(cursor.execute(query, *binds))[1]
            except pyodbc.Error as exc:
                print(f'{operation} DEMO_SKIPPED {odbc_failure(exc)}', flush=True)
            else:
                print(f'{operation} DEMO_ROWS={len(expected)}', flush=True)
                functional.append({'operation': operation, 'parameters': params, 'rows': expected})
        operations = {'ListarTiposVehiculo', 'ValidarEmpleadoCapturador', *writes,
                      *(entry['operation'] for entry in functional)}
        settings = Settings(jwt_key=secrets.token_urlsafe(48), connection_string=sql, station='1/2/3',
                            envelope_keys_path=profile / 'keys', devices={
            'encrypted-pilot': Device(station='1/2/3', secret_hash=hash_secret(device_secret), operations=operations),
        })
        print(f'OPERATIONS_REGISTERED={len(registered_operations(settings))}', flush=True)
        cursor.execute('''INSERT INTO dbo.PermisosEmpleado
            (Identificacion,Empleado,Clave,Capturador,JornadaZeta,Turno,Reimpresion,Calibracion,ReporteX,Codigo)
            VALUES (?, ?, ?, 1, 0, 0, 0, 0, 0, ?)''', fixture, 'LAB API_ONLY', password, 'API-ONLY')
        server = None
        try:
            server = TestServer(settings, profile, connect=connect)
            server.start()
            attempts = [
                {'operation': name, 'parameters': {'items': [fields] * repeat}, 'code': code}
                for name, (_, fields) in writes.items()
                for repeat, code in ((1, 'WRITE_OUTCOME_UNKNOWN'), (2, 'SQL_WRITE_FAILED'))
            ]
            subprocess.run([shutil.which('flutter.bat'), 'test', '--no-pub', '--dart-define=LOCAL_API_ONLY=true',
                            'test/core/local_api_only_test.dart', 'test/core/local_api_envelope_live_test.dart'],
                cwd=FLUTTER, timeout=150, check=True, env={**os.environ,
                    'ZENC_ENVELOPE_ORIGIN': f'https://127.0.0.1:{server.port}',
                    'ZENC_ENVELOPE_CA': str(profile / 'ca.pem'),
                    'ZENC_ENVELOPE_TEST_PEM': (profile / 'public.pem').read_text(encoding='ascii'),
                    'ZENC_ENVELOPE_DEVICE': device_secret, 'ZENC_ENVELOPE_ROWS': json.dumps(vehicles),
                    'ZENC_ENVELOPE_EMPLOYEE': fixture, 'ZENC_ENVELOPE_EMPLOYEE_PASSWORD': password,
                    'ZENC_ENVELOPE_FUNCTIONAL_READS': json.dumps(functional, default=str),
                    'ZENC_ENVELOPE_ROLLBACK_WRITES': json.dumps(attempts),
                })
            assert seen == writes.keys()
            for table, expected in baselines.items():
                assert sorted(map(str, rows(cursor, f'SELECT * FROM dbo.{table}'))) == expected
            print(f'ROLLBACK_CATALOGS=2 AUTH_EMPLOYEE=OK REAL_READS={1 + len(functional)}', flush=True)
        finally:
            if server is not None:
                server.close()
            cursor.execute('DELETE FROM dbo.PermisosEmpleado WHERE Identificacion=?', fixture)
            assert cursor.rowcount == 1
            assert cursor.execute('SELECT COUNT(*) FROM dbo.PermisosEmpleado WHERE Identificacion=?', fixture).fetchval() == 0
            print('SYNTHETIC_EMPLOYEE_REMOVED=1', flush=True)


try:
    validate()
except pyodbc.Error as exc:
    print('ODBC_FAILURE', odbc_failure(exc))
    raise SystemExit(1) from None
