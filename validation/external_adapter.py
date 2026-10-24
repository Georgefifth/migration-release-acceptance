"""Reviewed synthetic HTTP mapping for unchanged external SQL statements.

This is not an upstream application. Oracle labels are never loaded here.
"""
import json
import os
import sys
from pathlib import Path

from acceptance.http_client import Application
from acceptance.integration import Integration
from acceptance.workload import Workload


def configuration():
    path = Path(os.environ['VALIDATION_INPUT']).resolve()
    return path, json.loads(path.read_text())


class ExternalSQLApplication(Application):
    def environment(self):
        path, _ = configuration()
        return {'PATH': os.environ['PATH'], 'DATABASE_URL': self.dsn,
                'ACCEPTANCE_SCHEMA': self.schema, 'ACCEPTANCE_DISPOSABLE_DB': 'yes',
                'VALIDATION_INPUT': str(path)}

    def command(self, ready_file):
        return [sys.executable, '-m', 'validation.external_adapter', '--version',
                self.version, '--ready-file', str(ready_file)]


def integration():
    path, data = configuration()
    return Integration(
        application_factory=ExternalSQLApplication,
        workload=Workload(name=data['id'], entity='external SQL record',
                          fixtures=path.parent, **data['values'],
                          provenance=data['provenance'],
                          application_scope='Synthetic reviewed HTTP mapping over external SQL, not an upstream business application.'),
        candidates={data['id']: path.parent / 'candidate.sql'})


def serve():
    from psycopg import sql
    from acceptance import http_app
    from acceptance.adapters import RecordMissing
    _, data = configuration()

    class Repository:
        def __init__(self, column):
            self.column = sql.Identifier(column)
            self.table = sql.Identifier(data['table'])
            self.key = sql.Identifier(data.get('key', 'id'))

        def read(self, conn, key):
            row = conn.execute(sql.SQL('SELECT {} FROM {} WHERE {} = %s').format(
                self.column, self.table, self.key), (key,)).fetchone()
            if row is None:
                raise RecordMissing()
            return None if row[0] is None else str(row[0])

        def create(self, conn, key, value):
            conn.execute(sql.SQL('INSERT INTO {} ({}, {}) VALUES (%s, %s)').format(
                self.table, self.key, self.column), (key, value))

        def update(self, conn, key, value):
            conn.execute(sql.SQL('UPDATE {} SET {} = %s WHERE {} = %s').format(
                self.table, self.column, self.key), (value, key))

    http_app.OLD = Repository(data['old_column'])
    http_app.NEW = Repository(data['new_column'])
    http_app.main()


if __name__ == '__main__':
    serve()
