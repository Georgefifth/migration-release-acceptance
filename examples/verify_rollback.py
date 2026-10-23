"""Detect incorrect rollback values, including stale nonempty and valid empty data."""
from dataclasses import replace
import json
import os
from pathlib import Path
import sys

import psycopg

from acceptance.http_client import Application
from acceptance.report import write_reports
from acceptance.runner import run
from acceptance.workload import Workload


def factory_for(replacement, version='v1', match_value=None):
    class RollbackApplication(Application):
        starts = 0

        def start(self):
            self.starts += 1
            return super().start()

        def command(self, ready_file):
            if self.version == version and (version == 'v2' or self.starts > 1):
                return [sys.executable, '-m', 'examples.rollback_http_app',
                        '--version', self.version, '--ready-file', str(ready_file)]
            return super().command(ready_file)

        def environment(self):
            # Only synthetic fixture credentials/settings enter the child.
            environment = super().environment()
            environment.update(ACCEPTANCE_ROLLBACK_RESPONSE=replacement,
                               ACCEPTANCE_ROLLBACK_VERSION=version)
            if match_value is not None:
                environment['ACCEPTANCE_ROLLBACK_MATCH'] = match_value
            return {key: value for key, value in environment.items()
                if key in {'PATH', 'DATABASE_URL', 'ACCEPTANCE_SCHEMA',
                           'ACCEPTANCE_DISPOSABLE_DB', 'ACCEPTANCE_ROLLBACK_RESPONSE',
                           'ACCEPTANCE_ROLLBACK_VERSION', 'ACCEPTANCE_ROLLBACK_MATCH'}}

    return RollbackApplication


def main():
    output = Path('reports/rollback-values')
    results = []
    valid = True
    for name, factory, workload, expected in (
        ('normal', Application, Workload(), 'GO_WITHIN_SCOPE'),
        ('stale', factory_for(Workload().initial), Workload(), 'BLOCK'),
        ('corrupt', factory_for('wrong-synthetic-value'), Workload(), 'BLOCK'),
        ('empty', Application, replace(Workload(), old_update=''), 'GO_WITHIN_SCOPE'),
        ('paired-read-fails', factory_for('wrong-synthetic-value', 'v2', Workload().old_update),
         Workload(), 'BLOCK'),
    ):
        report = run('expand', os.environ['DATABASE_URL'],
                     application_factory=factory, workload=workload)
        write_reports(report, output / name)
        failed = [c['id'] for c in report['checks'] if c['status'] != 'PASS']
        expected_failures = (['old_update_to_new'] if name == 'paired-read-fails' else
                             ['rollback_read'] if expected == 'BLOCK' else [])
        passed = (report['verdict'] == expected and failed == expected_failures
                  and report['completed'] and report['cleanup_ok'])
        # Independently check removal of the exact schema owned by this run.
        with psycopg.connect(os.environ['DATABASE_URL']) as conn:
            removed = not conn.execute(
                'SELECT 1 FROM pg_namespace WHERE nspname = %s',
                (report['cleanup_evidence']['schema'],)).fetchone()
        valid = bool(passed and removed) and valid
        results.append(dict(case=name, expected=expected, actual=report['verdict'],
                            failed_checks=failed, completed=report['completed'],
                            cleanup_ok=report['cleanup_ok'], schema_removal_verified=removed,
                            run_id=report['run_id']))
        print(f'Rollback value {name}: {report["verdict"]}; failed={failed}; cleaned={removed}')
    output.mkdir(parents=True, exist_ok=True)
    (output / 'verification.json').write_text(json.dumps(
        dict(cases=results, all_expected=valid, independent_customer_validation=False), indent=2) + '\n')
    return 0 if valid else 1


if __name__ == '__main__':
    raise SystemExit(main())
