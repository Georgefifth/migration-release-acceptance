"""Runnable project-local adapter example using the synthetic reference app."""
import argparse
import json
import os
import sys
from pathlib import Path

from acceptance.http_client import Application
from acceptance.report import write_reports
from acceptance.runner import run


class ProjectApplication(Application):
    def command(self, ready_file):
        # Replace this with your reviewed v1/v2 launch commands. This example
        # deliberately keeps the same synthetic app, not a real customer system.
        return [sys.executable, '-m', 'acceptance.http_app', '--version', self.version,
                '--ready-file', str(ready_file)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', choices=['expand', 'breaking'], required=True)
    parser.add_argument('--output', type=Path, default=Path('reports/project-adapter'))
    args = parser.parse_args()
    if not os.environ.get('DATABASE_URL') or os.environ.get('ACCEPTANCE_DISPOSABLE_DB') != 'yes':
        parser.exit(2, 'DATABASE_URL and ACCEPTANCE_DISPOSABLE_DB=yes are required.\n')
    report = run(args.scenario, os.environ['DATABASE_URL'], application_factory=ProjectApplication)
    write_reports(report, args.output)
    print('ACCEPTANCE_REPORT_BEGIN')
    print(json.dumps(report))
    print('ACCEPTANCE_REPORT_END')
    return {'GO_WITHIN_SCOPE': 0, 'BLOCK': 1, 'INCONCLUSIVE': 2}[report['verdict']]


if __name__ == '__main__':
    raise SystemExit(main())
