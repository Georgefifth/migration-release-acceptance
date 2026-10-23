"""Regression-test the harness using known unsafe and compatible fixtures."""
import argparse
import os
from pathlib import Path
from .report import write_reports
from .runner import run


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('reports'))
    args = parser.parse_args(argv)
    dsn = os.environ['DATABASE_URL']
    for scenario, expected in [('breaking', 'BLOCK'), ('expand', 'GO_WITHIN_SCOPE')]:
        result = run(scenario, dsn)
        write_reports(result, args.output)
        if result['verdict'] != expected:
            raise AssertionError(f'{scenario}: expected {expected}, got {result["verdict"]}')
        applications = result['applications']
        if (result['transport'] != 'HTTP' or len(applications) != 3
                or len({app['pid'] for app in applications}) != 3
                or applications[-1].get('phase') != 'rollback'):
            raise AssertionError('Independent application lifecycle evidence missing')
        checks = {c['id']: c for c in result['checks']}
        # Distinguish the compatibility blind spot from simply broken SQL/new code.
        for name in ['migration', 'new_read', 'new_write']:
            if checks[name]['status'] != 'PASS':
                raise AssertionError(f'{scenario}: {name} must pass')
        if scenario == 'breaking':
            for name in ['old_read', 'old_write', 'old_to_new', 'new_to_old',
                         'new_update_to_old', 'old_update_to_new',
                         'rollback_read', 'rollback_new_data']:
                if checks[name]['status'] != 'FAIL' or checks[name]['sqlstate'] != '42703':
                    raise AssertionError(f'Expected missing-column evidence for {name}')
        print(f'{scenario}: verified {expected} with {len(checks)} executed probes')


if __name__ == '__main__':
    main()
