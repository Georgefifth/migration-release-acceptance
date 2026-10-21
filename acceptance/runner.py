"""Run trusted reference fixtures against a disposable PostgreSQL database."""
import argparse
import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .http_client import Application, ApplicationError
from .report import write_reports

ROOT = Path(__file__).resolve().parent.parent
CHECK_IDS = (
    'applications_started', 'baseline_read', 'baseline_write', 'migration', 'new_application_started', 'new_read', 'new_write',
    'old_read', 'old_write', 'old_to_new', 'new_to_old',
    'new_update_to_old', 'old_update_to_new', 'rollback_restart', 'rollback_read', 'rollback_new_data',
)
COMPATIBILITY_STATES = {'42703', '42P01', '23502', '23505', '23514', 'P0001'}


def verdict(report):
    checks = report.get('checks', [])
    ids = [c['id'] for c in checks]
    if (not report.get('completed') or not report.get('cleanup_ok')
            or len(ids) != len(CHECK_IDS) or set(ids) != set(CHECK_IDS)):
        return 'INCONCLUSIVE'
    if any(c['status'] != 'PASS' for c in checks
           if c['id'] in {'applications_started', 'new_application_started', 'baseline_read', 'baseline_write', 'migration', 'rollback_restart'}):
        return 'INCONCLUSIVE'
    failures = [c for c in checks if c['status'] != 'PASS']
    if any(c.get('failure_kind') != 'compatibility' for c in failures):
        return 'INCONCLUSIVE'
    return 'BLOCK' if failures else 'GO_WITHIN_SCOPE'


def equal(actual, expected):
    if actual != expected:
        # No row contents are included in the error or report.
        raise AssertionError('Business result mismatch')


def roundtrip(conn, adapter, customer_id):
    value = 'created@example.test'
    adapter.create(conn, customer_id, value)
    equal(adapter.read(conn, customer_id), value)


def run(scenario, dsn, application_factory=Application):
    import psycopg
    from psycopg import sql

    if os.environ.get('ACCEPTANCE_DISPOSABLE_DB') != 'yes':
        raise ValueError('Set ACCEPTANCE_DISPOSABLE_DB=yes for a disposable test DB')
    if scenario not in {'breaking', 'expand'}:
        raise ValueError('Unsupported reference scenario')
    baseline = (ROOT / 'fixtures/baseline.sql').read_text()
    migration = (ROOT / f'fixtures/{scenario}.sql').read_text()
    report = {
        'schema_version': 2,
        'transport': 'HTTP',
        'application_factory': getattr(application_factory, '__module__', 'unknown') + ':'
        + getattr(application_factory, '__qualname__', type(application_factory).__qualname__),
        'applications': [],
        'run_id': str(uuid.uuid4()),
        'scenario': scenario,
        'commit': os.environ.get('CI_COMMIT_SHA', 'local-development'),
        'pipeline_url': os.environ.get('CI_PIPELINE_URL', ''),
        'created_at': datetime.now(timezone.utc).isoformat(),
        'fixture_sha256': hashlib.sha256((baseline + '\n' + migration).encode()).hexdigest(),
        'checks': [], 'completed': False, 'cleanup_ok': False,
        'limitations': [
            'Synthetic customer records only; no production data or traffic.',
            'Two synthetic HTTP app processes using separate per-request database connections.',
            'Sequential interleavings; no concurrent transactions or load test.',
            'No lock-duration, large backfill, replication, or production deployment verification.',
            'Rollback means returning to v1 code on the migrated schema, not undoing SQL.',
            'GO applies only to this fixture and these declared probes.',
        ],
    }
    schema = 'acceptance_' + uuid.uuid4().hex
    conn = None
    created = False
    # A reviewed project-local callable may supply the two application adapters.
    # Register before starting so cleanup also covers partial startup failures.
    applications = []
    OLD = NEW = None

    def start_application(app, version, phase=None):
        identity = app.start()
        if (not isinstance(identity, dict) or identity.get('version') != version
                or identity.get('transport') != 'HTTP'
                or not isinstance(identity.get('pid'), int)
                or identity['pid'] != app.process.pid or app.process.poll() is not None):
            raise RuntimeError('Invalid application lifecycle evidence')
        # Adapters cannot accidentally put extra fields (rows/DSNs) in artifacts.
        evidence = dict(version=version, pid=identity['pid'], transport='HTTP')
        if phase:
            evidence['phase'] = phase
        report['applications'].append(evidence)
        return evidence

    def check(check_id, stage, version, operation, fn):
        start = time.monotonic()
        item = dict(id=check_id, stage=stage, version=version, operation=operation)
        try:
            with conn.transaction():
                fn()
            item['status'] = 'PASS'
        except (psycopg.Error, ApplicationError) as exc:
            item.update(status='FAIL', sqlstate=exc.sqlstate,
                        failure_kind='compatibility' if exc.sqlstate in COMPATIBILITY_STATES
                        else 'infrastructure_or_unknown')
        except AssertionError:
            item.update(status='FAIL', failure_kind='compatibility', sqlstate=None)
        item['duration_ms'] = round((time.monotonic() - start) * 1000, 2)
        report['checks'].append(item)
        return item['status'] == 'PASS'

    try:
        OLD = application_factory('v1', schema, dsn)
        applications.append(OLD)
        NEW = application_factory('v2', schema, dsn)
        applications.append(NEW)
        for application in applications:
            for method in ('start', 'stop', 'read', 'create', 'update'):
                if not callable(getattr(application, method, None)):
                    raise TypeError('Application adapter is missing a required method')
        # Caller must supply a dedicated disposable DB; SQL fixtures are trusted code.
        conn = psycopg.connect(dsn, autocommit=True, connect_timeout=10)
        conn.execute("SET statement_timeout = '5s'")
        conn.execute("SET lock_timeout = '2s'")
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        created = True
        conn.execute(sql.SQL('SET search_path TO {}, pg_catalog').format(sql.Identifier(schema)))
        with conn.transaction():
            conn.execute(baseline)
        report['postgres_version'] = conn.info.server_version
        if not check('applications_started', 'baseline', 'v1', 'Start independent old HTTP application',
                     lambda: start_application(OLD, 'v1')):
            return report
        if not check('baseline_read', 'baseline', 'v1', 'Read existing customer',
                     lambda: equal(OLD.read(conn, 1), 'initial@example.test')):
            return report
        if not check('baseline_write', 'baseline', 'v1', 'Create and read customer',
                     lambda: roundtrip(conn, OLD, 100)):
            return report
        if not check('migration', 'migration', '-', 'Apply candidate SQL',
                     lambda: conn.execute(migration)):
            return report
        if not check('new_application_started', 'target', 'v2', 'Start independent new HTTP application',
                     lambda: start_application(NEW, 'v2')):
            return report
        check('new_read', 'target', 'v2', 'Read migrated customer',
              lambda: equal(NEW.read(conn, 1), 'initial@example.test'))
        check('new_write', 'target', 'v2', 'Create and read customer',
              lambda: roundtrip(conn, NEW, 2))
        check('old_read', 'rollout', 'v1', 'Read migrated customer',
              lambda: equal(OLD.read(conn, 1), 'initial@example.test'))
        check('old_write', 'rollout', 'v1', 'Create and read customer',
              lambda: roundtrip(conn, OLD, 3))

        def old_to_new():
            OLD.create(conn, 10, 'old-write@example.test')
            equal(NEW.read(conn, 10), 'old-write@example.test')

        def new_to_old():
            NEW.create(conn, 11, 'new-write@example.test')
            equal(OLD.read(conn, 11), 'new-write@example.test')

        def new_update_to_old():
            NEW.update(conn, 1, 'new-update@example.test')
            equal(OLD.read(conn, 1), 'new-update@example.test')

        def old_update_to_new():
            OLD.update(conn, 1, 'old-update@example.test')
            equal(NEW.read(conn, 1), 'old-update@example.test')

        check('old_to_new', 'mixed', 'v1 → v2', 'Old creates; new reads', old_to_new)
        check('new_to_old', 'mixed', 'v2 → v1', 'New creates; old reads', new_to_old)
        check('new_update_to_old', 'mixed', 'v2 → v1', 'New updates; old reads', new_update_to_old)
        check('old_update_to_new', 'mixed', 'v1 → v2', 'Old updates; new reads', old_update_to_new)
        def restart_old():
            previous_pid = OLD.process.pid
            equal(NEW.stop(), True)
            equal(OLD.stop(), True)
            identity = start_application(OLD, 'v1', phase='rollback')
            equal(identity['pid'] != previous_pid, True)

        if not check('rollback_restart', 'app_rollback', 'v1',
                     'Stop both apps; restart v1; verify new process identity', restart_old):
            return report
        check('rollback_read', 'app_rollback', 'v1', 'Read pre-existing data after rollout',
              lambda: equal(bool(OLD.read(conn, 1)), True))
        check('rollback_new_data', 'app_rollback', 'v1', 'Read data committed by v2',
              lambda: equal(OLD.read(conn, 2), 'created@example.test'))
        report['completed'] = True
    except psycopg.Error as exc:
        # Do not serialize exceptions: server messages can contain rows/credentials.
        report['error'] = {'kind': 'database_setup_or_connection', 'sqlstate': exc.sqlstate}
    except Exception as exc:
        report['error'] = {'kind': type(exc).__name__}
    finally:
        processes_stopped = True
        for app in applications:
            try:
                processes_stopped = app.stop() and processes_stopped
            except Exception:
                processes_stopped = False
        if conn is not None:
            try:
                if created:
                    # Only drop the fresh random schema created by this exact run.
                    conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
                report['cleanup_ok'] = processes_stopped
            except psycopg.Error:
                report['cleanup_ok'] = False
            finally:
                conn.close()
        report['verdict'] = verdict(report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', choices=['breaking', 'expand'], required=True)
    parser.add_argument('--output', type=Path, default=Path('reports'))
    args = parser.parse_args()
    dsn = os.environ.get('DATABASE_URL')
    if not dsn or os.environ.get('ACCEPTANCE_DISPOSABLE_DB') != 'yes':
        parser.exit(2, 'DATABASE_URL and ACCEPTANCE_DISPOSABLE_DB=yes are required.\n')
    report = run(args.scenario, dsn)
    write_reports(report, args.output)
    # Bounded synthetic evidence is also visible to Duo's job-log tool.
    print('ACCEPTANCE_REPORT_BEGIN')
    print(json.dumps(report))
    print('ACCEPTANCE_REPORT_END')
    return {'GO_WITHIN_SCOPE': 0, 'BLOCK': 1, 'INCONCLUSIVE': 2}[report['verdict']]


if __name__ == '__main__':
    raise SystemExit(main())
