"""Inject bounded test faults; preserve INCONCLUSIVE and verify owned cleanup."""
from dataclasses import replace
import json
import os
from pathlib import Path
import re
import socket
import tempfile
from unittest.mock import patch

import psycopg
from psycopg import sql

from acceptance.diagnostics import troubleshooting
from acceptance.report import write_reports
from acceptance.runner import run
from acceptance.workload import Workload

PRIVATE = 'private-test-detail-must-not-enter-evidence'


def save(case, report, expected_code):
    assert report['verdict'] == 'INCONCLUSIVE', case
    assert expected_code in {i['code'] for i in troubleshooting(report)}, case
    output = Path('reports/failure-cases') / case
    write_reports(report, output)
    for suffix in ('json', 'html', 'md'):
        text = (output / (report['scenario'] + '.' + suffix)).read_text()
        assert PRIVATE not in text and 'postgresql://' not in text
    print(f'Fault {case}: INCONCLUSIVE; {expected_code}; schema={report["cleanup_evidence"]["schema_state"]}')


def main():
    dsn = os.environ['DATABASE_URL']
    if os.environ.get('ACCEPTANCE_DISPOSABLE_DB') != 'yes':
        raise RuntimeError('Use a disposable database')
    original_connect = psycopg.connect
    with socket.socket() as reserved:
        reserved.bind(('127.0.0.1', 0))  # Reserved, deliberately not listening.
        unavailable = f'postgresql://acceptance:synthetic@127.0.0.1:{reserved.getsockname()[1]}/acceptance'
        report = run('expand', unavailable)
        assert not report['checks'] and report['cleanup_ok']
        assert report['error_context']['phase'] == 'database_connection'
        assert report['cleanup_evidence']['schema_state'] == 'not_requested'
        save('database-unavailable', report, 'database_connection')

    with tempfile.TemporaryDirectory(prefix='acceptance-fault-sql-') as temporary:
        directory = Path(temporary)
        invalid = directory / 'invalid.sql'
        invalid.write_text('THIS IS NOT VALID SQL;')
        report = run('invalid-candidate', dsn, migration_path=invalid)
        assert report['cleanup_ok'] and not report['completed']
        assert next(c for c in report['checks'] if c['id'] == 'migration')['status'] == 'FAIL'
        save('candidate-sql', report, 'candidate_execution')
        (directory / 'baseline.sql').write_text(invalid.read_text())
        report = run('invalid-baseline', dsn, workload=replace(Workload(), fixtures=directory),
                     migration_path=Workload().fixtures / 'expand.sql')
        assert report['cleanup_ok'] and report['error_context']['phase'] == 'baseline_setup'
        save('baseline-sql', report, 'baseline_setup')

    class CleanupFault:
        def __init__(self, mode, *args, **kwargs):
            self.connection = original_connect(*args, **kwargs)
            self.mode = mode

        def __getattr__(self, key):
            return getattr(self.connection, key)

        def execute(self, statement, *args, **kwargs):
            text = statement.as_string(self.connection) if hasattr(statement, 'as_string') else statement
            if self.mode == 'drop' and text.startswith('DROP SCHEMA'):
                raise psycopg.OperationalError(PRIVATE)
            result = self.connection.execute(statement, *args, **kwargs)
            if self.mode == 'create-ack' and text.startswith('CREATE SCHEMA'):
                # Server-side creation completed, but the caller did not receive
                # a usable success result. Cleanup must still target that schema.
                raise psycopg.OperationalError(PRIVATE)
            return result

        def close(self):
            self.connection.close()
            if self.mode == 'close':
                raise RuntimeError(PRIVATE)

    for mode in ('create-ack', 'drop', 'close'):
        with patch('psycopg.connect', side_effect=lambda *a, **k: CleanupFault(mode, *a, **k)):
            report = run('expand', dsn)
        if mode == 'create-ack':
            assert not report['completed'] and not report['checks'] and report['cleanup_ok']
            assert report['cleanup_evidence']['schema_state'] == 'removed'
            save('schema-create-ack', report, 'schema_setup')
        else:
            assert report['completed'] and all(c['status'] == 'PASS' for c in report['checks'])
            assert not report['cleanup_ok']
            save('cleanup-' + mode, report, 'cleanup_unconfirmed')
        schema = report['cleanup_evidence']['schema']
        assert re.fullmatch(r'acceptance_[0-9a-f]{32}', schema)
        # Repair only this injected fault's freshly generated owned schema.
        # The runner must first have reported uncertainty, never a scoped GO.
        with original_connect(dsn, autocommit=True) as connection:
            exists = connection.execute('SELECT 1 FROM pg_namespace WHERE nspname = %s', (schema,)).fetchone()
            assert bool(exists) == (mode == 'drop')
            if exists:
                connection.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
    with original_connect(dsn) as connection:
        assert connection.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'acceptance_%'").fetchone()[0] == 0
    print('Injected faults verified; independent query found zero remaining test schemas.')


if __name__ == '__main__':
    main()
