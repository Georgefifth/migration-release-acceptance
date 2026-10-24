"""Own fixture process lifetimes and send real loopback HTTP requests."""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, ProxyHandler, build_opener


class ApplicationError(Exception):
    def __init__(self, sqlstate=None, reason=None):
        self.sqlstate = sqlstate if isinstance(sqlstate,str) and re.fullmatch(r'[0-9A-Z]{5}',sqlstate) else None
        self.reason = reason if reason == 'record_missing' else None
        super().__init__()  # Never preserve unvalidated arguments as exception text.


class Application:
    def __init__(self, version, schema, dsn):
        self.version = version
        self.schema = schema
        self.dsn = dsn
        self.process = None
        self.directory = None
        self.opener = build_opener(ProxyHandler({}))

    def command(self, ready_file):
        """Override only for a trusted app implementing the documented test protocol."""
        return [sys.executable, '-m', 'acceptance.http_app', '--version', self.version,
                '--ready-file', str(ready_file)]

    def environment(self):
        return dict(os.environ, ACCEPTANCE_SCHEMA=self.schema, DATABASE_URL=self.dsn)

    def start(self):
        self.directory = tempfile.TemporaryDirectory(prefix='acceptance-http-')
        ready = Path(self.directory.name) / 'ready.json'
        environment = self.environment()
        self.process = subprocess.Popen(
            self.command(ready), env=environment,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        deadline = time.monotonic() + 15
        while not ready.exists():
            if self.process.poll() is not None:
                raise RuntimeError('Application exited before readiness')
            if time.monotonic() >= deadline:
                raise TimeoutError('Application readiness timeout')
            time.sleep(0.05)
        self.url = 'http://127.0.0.1:' + str(json.loads(ready.read_text())['port'])
        health = self.request('GET', '/health')
        if health != {'version': self.version, 'pid': self.process.pid}:
            raise RuntimeError('Application identity mismatch')
        return dict(version=self.version, pid=self.process.pid, transport='HTTP')

    def stop(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        if self.directory is not None:
            self.directory.cleanup()
        return self.process is None or self.process.poll() is not None

    def request(self, method, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode()
        request = Request(self.url + path, data=data, method=method,
                          headers={'Content-Type': 'application/json'})
        try:
            with self.opener.open(request, timeout=10) as response:
                return json.load(response)
        except HTTPError as exc:
            # Only a validated SQLSTATE or exact reviewed protocol marker crosses
            # into evidence. A generic HTTP 404 does not identify a missing row.
            try:
                body = json.load(exc)
                state = body.get('sqlstate')
                reason = 'record_missing' if exc.code == 404 and body.get('error') == 'record_missing' else None
            except (ValueError, AttributeError):
                state,reason = None,None
            raise ApplicationError(state,reason=reason) from None

    def read(self, _conn, customer_id):
        return self.request('GET', f'/customers/{customer_id}')['email']

    def create(self, _conn, customer_id, email):
        self.request('POST', f'/customers/{customer_id}', {'email': email})

    def update(self, _conn, customer_id, email):
        self.request('PATCH', f'/customers/{customer_id}', {'email': email})
