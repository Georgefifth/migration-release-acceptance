"""Accept real upstream login and item CRUD routes across a reviewed DB change."""
import argparse
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request

from acceptance.http_client import Application
from acceptance.report import write_reports
from acceptance.runner import run
from acceptance.workload import Workload
from .fastapi_launcher import SEED_ID

ROOT = Path(__file__).resolve().parent.parent


def isolated_environment(environment):
    # Do not forward CI job tokens or developer credentials into upstream apps.
    required = ('PATH', 'DATABASE_URL', 'ACCEPTANCE_SCHEMA', 'ACCEPTANCE_DISPOSABLE_DB')
    return {key: environment[key] for key in required if key in environment}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', choices=['expand', 'breaking'], required=True)
    args = parser.parse_args()
    shared_ids = {1: SEED_ID}
    admin_password = secrets.token_urlsafe(24)
    jwt_secret = secrets.token_urlsafe(48)

    class UpstreamApplication(Application):
        def environment(self):
            environment = isolated_environment(super().environment())
            environment.update(
                PGOPTIONS=f'-c search_path={self.schema},pg_catalog -c statement_timeout=5000 -c lock_timeout=2000',
                PROJECT_NAME='Disposable upstream acceptance',
                FIRST_SUPERUSER='acceptance@example.com', FIRST_SUPERUSER_PASSWORD=admin_password,
                SECRET_KEY=jwt_secret, SENTRY_DSN='', SMTP_HOST='')
            return environment

        def command(self, ready_file):
            return [sys.executable, '-m', 'integrations.fastapi_launcher', '--mode', 'serve',
                    '--version', self.version, '--ready-file', str(ready_file)]

        def request(self, method, path, payload=None):
            if path == '/health':
                path = '/__acceptance/health'
            return super().request(method, path, payload)

        def start(self):
            identity = super().start()
            request = Request(self.url + '/api/v1/login/access-token', method='POST',
                              data=urlencode({'username': 'acceptance@example.com', 'password': admin_password}).encode(),
                              headers={'Content-Type': 'application/x-www-form-urlencoded'})
            with self.opener.open(request, timeout=10) as response:
                token = json.load(response)['access_token']
            # Kept in memory only. No reports or logs contain auth tokens.
            self.opener.addheaders = [('Authorization', 'Bearer ' + token)]
            return identity

        def read(self, _conn, record_id):
            return self.request('GET', '/api/v1/items/' + shared_ids[record_id])['title']

        def create(self, _conn, record_id, value):
            result = self.request('POST', '/api/v1/items/', {'title': value, 'description': 'Synthetic acceptance item'})
            shared_ids[record_id] = result['id']

        def update(self, _conn, record_id, value):
            self.request('PUT', '/api/v1/items/' + shared_ids[record_id], {'title': value})

    def initialize(schema, dsn):
        app = UpstreamApplication('v1', schema, dsn)
        subprocess.run([sys.executable, '-m', 'integrations.fastapi_launcher', '--mode', 'initialize'],
                       env=app.environment(), check=True, timeout=60,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    manifest = json.loads((ROOT / '.upstream/manifest.json').read_text())
    workload = Workload(
        name='fastapi-upstream-items', entity='project item',
        fixtures=ROOT / 'integrations/fastapi_fixtures', initialize=initialize,
        initial='Existing project item', created='Created project item',
        old_write='Created by old app', new_write='Created by new app',
        old_update='Updated by old app', new_update='Updated by new app',
        provenance=manifest,
        application_scope='Two independent instances of the pinned upstream FastAPI backend with real login and item CRUD routes; synthetic data.')
    report = run(args.scenario, os.environ['DATABASE_URL'], application_factory=UpstreamApplication, workload=workload)
    write_reports(report, ROOT / 'reports/upstream')
    print('ACCEPTANCE_REPORT_BEGIN')
    print(json.dumps(report))
    print('ACCEPTANCE_REPORT_END')
    expected = 'BLOCK' if args.scenario == 'breaking' else 'GO_WITHIN_SCOPE'
    # This command verifies a known integration case, never release approval.
    if report['verdict'] != expected:
        return 2
    if args.scenario == 'breaking':
        failed = [c for c in report['checks'] if c['status'] != 'PASS']
        if len(failed) != 8 or any(c.get('sqlstate') != '42703' for c in failed):
            return 2
    print(f'Upstream integration verified: {args.scenario} => {expected}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
