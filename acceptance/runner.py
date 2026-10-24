"""Run trusted reference fixtures against a disposable PostgreSQL database."""
import argparse
from contextlib import nullcontext
import hashlib
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .http_client import Application, ApplicationError
from .report import write_reports
from .workload import Workload
from .diagnostics import summary_lines

ROOT = Path(__file__).resolve().parent.parent
CHECK_IDS = (
    'applications_started', 'baseline_read', 'baseline_write', 'migration', 'new_application_started', 'new_read', 'new_write',
    'old_read', 'old_write', 'old_to_new', 'new_to_old',
    'new_update_to_old', 'old_update_to_new', 'rollback_restart', 'rollback_read', 'rollback_new_data',
)
# Application requests rejected by a migrated length or foreign-key constraint
# are compatibility failures. Baseline/migration failures still remain
# INCONCLUSIVE through verdict()'s lifecycle guard.
COMPATIBILITY_STATES = {'42703', '42P01', '22001', '22003', '22P02', '23502', '23503', '23505', '23514', '42501', '428C9', 'P0001'}


def verdict(report):
    checks = report.get('checks', [])
    ids = [c['id'] for c in checks]
    if (not report.get('completed') or not report.get('cleanup_ok')
            or len(ids) != len(CHECK_IDS) or set(ids) != set(CHECK_IDS)):
        return 'INCONCLUSIVE'
    if any(c['status'] != 'PASS' for c in checks
           if c['id'] in {'applications_started', 'new_application_started', 'baseline_read', 'baseline_write', 'migration', 'rollback_restart'}):
        return 'INCONCLUSIVE'
    by_id = {c['id']: c for c in checks}
    for c in checks:
        if c['status'] == 'SKIP':
            parent = by_id.get('new_write', {})
            if (c['id'] != 'rollback_new_data' or c.get('depends_on') != 'new_write'
                    or c.get('reason_code') != 'create_not_acknowledged'
                    or c.get('failure_kind') != 'dependency'
                    or parent.get('status') != 'FAIL'
                    or parent.get('write_acknowledged') is not False):
                return 'INCONCLUSIVE'
        elif c['status'] not in {'PASS', 'FAIL'}:
            return 'INCONCLUSIVE'
    failures = [c for c in checks if c['status'] == 'FAIL']
    if any(c.get('failure_kind') != 'compatibility' for c in failures):
        return 'INCONCLUSIVE'
    return 'BLOCK' if failures else 'GO_WITHIN_SCOPE'


def equal(actual, expected):
    if actual != expected:
        # No row contents are included in the error or report.
        raise AssertionError('Business result mismatch')


def roundtrip(conn, adapter, customer_id, value='created@example.test'):
    adapter.create(conn, customer_id, value)
    equal(adapter.read(conn, customer_id), value)


def run(scenario, dsn, application_factory=Application, workload=None, migration_path=None, migration_transactional=True):
    import psycopg
    from psycopg import sql

    if type(migration_transactional) is not bool:
        raise ValueError('migration_transactional must be a boolean')
    if os.environ.get('ACCEPTANCE_DISPOSABLE_DB') != 'yes':
        raise ValueError('Set ACCEPTANCE_DISPOSABLE_DB=yes for a disposable test DB')
    if migration_path is None and scenario not in {'breaking', 'expand'}:
        raise ValueError('Unsupported reference scenario')
    if not isinstance(scenario, str) or not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', scenario):
        raise ValueError('Invalid candidate name')
    workload = workload or Workload()
    baseline = (workload.fixtures / 'baseline.sql').read_text()
    migration = (migration_path if migration_path is not None else workload.fixtures / f'{scenario}.sql').read_text()
    report = {
        'schema_version': 3,
        'migration_transactional': migration_transactional,
        'transport': 'HTTP',
        'workload': workload.name,
        'provenance': workload.provenance,
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
        'coverage': {'workflow': 'One normalized string CRUD mapping',
                     'operations': ['read', 'create', 'update'],
                     'unmapped_business_invariants': 'not_checked'},
        'limitations': [
            f'Synthetic {workload.entity} records only; no production data or traffic.',
            workload.application_scope,
            'Sequential interleavings; no concurrent transactions or load test.',
            'No lock-duration, large backfill, replication, or production deployment verification.',
            'Rollback means returning to v1 code on the migrated schema, not undoing SQL.',
            'GO applies only to this fixture and these declared probes.',
            'Unmapped fields, derived values and other business invariants are not checked.',
        ],
    }
    if not migration_transactional:
        report['limitations'].append('Candidate SQL has no runner transaction wrapper. Multi-statement strings may still use an implicit transaction; partial effects are not automatically reversed.')
    schema = 'acceptance_' + uuid.uuid4().hex
    cleanup = dict(schema=schema, schema_state='not_requested',
                   applications_stopped=None, connection_closed=None)
    report['cleanup_evidence'] = cleanup
    phase = 'adapter_construction'
    active_check = None
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

    def check(check_id, stage, version, operation, fn, transactional=True):
        nonlocal phase, active_check
        phase, active_check = 'application_checks', check_id
        start = time.monotonic()
        item = dict(id=check_id, stage=stage, version=version, operation=operation.replace('customer', workload.entity))
        try:
            with conn.transaction() if transactional else nullcontext():
                fn()
            item['status'] = 'PASS'
        except (psycopg.Error, ApplicationError) as exc:
            reason = exc.reason if isinstance(exc,ApplicationError) else None
            item.update(status='FAIL', sqlstate=exc.sqlstate,
                        failure_kind='compatibility' if exc.sqlstate in COMPATIBILITY_STATES or reason == 'record_missing'
                        else 'infrastructure_or_unknown')
            if reason:
                item['failure_reason'] = reason
        except AssertionError:
            item.update(status='FAIL', failure_kind='compatibility', sqlstate=None)
        except Exception:
            item.update(status='FAIL', failure_kind='infrastructure_or_unknown', sqlstate=None)
            raise
        finally:
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
        phase = 'database_connection'
        conn = psycopg.connect(dsn, autocommit=True, connect_timeout=10)
        phase = 'schema_setup'
        conn.execute("SET statement_timeout = '5s'")
        conn.execute("SET lock_timeout = '2s'")
        try:
            role = conn.execute('SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone()
            report['database_role_capabilities'] = dict(connection_scope='runner_only', available=role is not None)
            if role is not None:
                report['database_role_capabilities'].update(superuser=role[0],bypass_rls=role[1])
                if any(role):
                    report['limitations'].append('The runner connection can bypass row-level security. Application-role RLS coverage requires separate evidence.')
        except psycopg.errors.InsufficientPrivilege:
            report['database_role_capabilities'] = dict(connection_scope='runner_only',available=False)
        report['limitations'].append('Runner role evidence does not identify application roles. Table owners can bypass RLS without FORCE ROW LEVEL SECURITY.')
        cleanup['schema_state'] = 'unconfirmed'
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        created = True
        cleanup['schema_state'] = 'present'
        conn.execute(sql.SQL('SET search_path TO {}, pg_catalog').format(sql.Identifier(schema)))
        phase = 'baseline_setup'
        with conn.transaction():
            conn.execute(baseline)
        if workload.initialize is not None:
            phase = 'workload_initialization'
            workload.initialize(schema, dsn)
        report['postgres_version'] = conn.info.server_version
        if not check('applications_started', 'baseline', 'v1', 'Start independent old HTTP application',
                     lambda: start_application(OLD, 'v1')):
            return report
        if not check('baseline_read', 'baseline', 'v1', 'Read existing customer',
                     lambda: equal(OLD.read(conn, 1), workload.initial)):
            return report
        if not check('baseline_write', 'baseline', 'v1', 'Create and read customer',
                     lambda: roundtrip(conn, OLD, 100, workload.created)):
            return report
        if not check('migration', 'migration', '-', 'Apply candidate SQL',
                     lambda: conn.execute(migration), transactional=migration_transactional):
            return report
        if not check('new_application_started', 'target', 'v2', 'Start independent new HTTP application',
                     lambda: start_application(NEW, 'v2')):
            return report
        check('new_read', 'target', 'v2', 'Read migrated customer',
              lambda: equal(NEW.read(conn, 1), workload.initial))
        new_write_acknowledged = False

        def create_new():
            nonlocal new_write_acknowledged
            NEW.create(conn, 2, workload.created)
            new_write_acknowledged = True
            equal(NEW.read(conn, 2), workload.created)

        check('new_write', 'target', 'v2', 'Create and read customer', create_new)
        report['checks'][-1]['write_acknowledged'] = new_write_acknowledged
        check('old_read', 'rollout', 'v1', 'Read migrated customer',
              lambda: equal(OLD.read(conn, 1), workload.initial))
        check('old_write', 'rollout', 'v1', 'Create and read customer',
              lambda: roundtrip(conn, OLD, 3, workload.created))

        def old_to_new():
            OLD.create(conn, 10, workload.old_write)
            equal(NEW.read(conn, 10), workload.old_write)

        def new_to_old():
            NEW.create(conn, 11, workload.new_write)
            equal(OLD.read(conn, 11), workload.new_write)

        # Record only values whose update returned a committed success. A later
        # paired read may fail, but that does not undo the acknowledged write.
        rollback_expected = workload.initial

        def new_update_to_old():
            nonlocal rollback_expected
            NEW.update(conn, 1, workload.new_update)
            rollback_expected = workload.new_update
            equal(OLD.read(conn, 1), workload.new_update)

        def old_update_to_new():
            nonlocal rollback_expected
            OLD.update(conn, 1, workload.old_update)
            rollback_expected = workload.old_update
            equal(NEW.read(conn, 1), workload.old_update)

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
        check('rollback_read', 'app_rollback', 'v1', 'Read latest acknowledged value after rollout',
              lambda: equal(OLD.read(conn, 1), rollback_expected))
        if new_write_acknowledged:
            check('rollback_new_data', 'app_rollback', 'v1', 'Read data committed by v2',
                  lambda: equal(OLD.read(conn, 2), workload.created))
        else:
            report['checks'].append(dict(id='rollback_new_data', stage='app_rollback',
                version='v1', operation='Read data committed by v2', status='SKIP',
                failure_kind='dependency', depends_on='new_write',
                reason_code='create_not_acknowledged', duration_ms=0))
        report['completed'] = True
    except psycopg.Error as exc:
        # Do not serialize exceptions: server messages can contain rows/credentials.
        report['error'] = {'kind': 'database_setup_or_connection', 'sqlstate': exc.sqlstate}
        report['error_context'] = dict(phase=phase, check_id=active_check)
    except Exception as exc:
        report['error'] = {'kind': type(exc).__name__}
        report['error_context'] = dict(phase=phase, check_id=active_check)
    finally:
        processes_stopped = True
        for app in applications:
            try:
                processes_stopped = app.stop() and processes_stopped
            except Exception:
                processes_stopped = False
        cleanup['applications_stopped'] = processes_stopped
        if conn is not None:
            try:
                if created or cleanup['schema_state'] == 'unconfirmed':
                    # Only drop the fresh random schema created by this exact run.
                    conn.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(sql.Identifier(schema)))
                    cleanup['schema_state'] = 'removed'
            except Exception:
                cleanup['schema_state'] = 'unconfirmed'
            finally:
                try:
                    conn.close()
                    cleanup['connection_closed'] = True
                except Exception:
                    cleanup['connection_closed'] = False
        report['cleanup_ok'] = (processes_stopped
                                and cleanup['schema_state'] in {'not_requested', 'removed'}
                                and cleanup['connection_closed'] is not False
                                and phase != 'adapter_construction')
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
    print('\n'.join(summary_lines(report)))
    return {'GO_WITHIN_SCOPE': 0, 'BLOCK': 1, 'INCONCLUSIVE': 2}[report['verdict']]


if __name__ == '__main__':
    raise SystemExit(main())
