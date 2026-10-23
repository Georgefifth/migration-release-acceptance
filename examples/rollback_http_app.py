"""Controlled stale/corrupt response fixture; never a production application."""
import os

from acceptance import http_app


def main():
    version = os.environ.get('ACCEPTANCE_ROLLBACK_VERSION', 'v1')
    original = http_app.OLD if version == 'v1' else http_app.NEW
    match_value = os.environ.get('ACCEPTANCE_ROLLBACK_MATCH')
    replacement = os.environ['ACCEPTANCE_ROLLBACK_RESPONSE']

    class ChangedRead:
        def read(self, conn, record_id):
            actual = original.read(conn, record_id)
            # Still execute a real database read, but simulate a restarted old
            # application exposing a stale cache or incorrect field mapping.
            return replacement if record_id == 1 and (match_value is None or actual == match_value) else actual

        def create(self, conn, record_id, value):
            return original.create(conn, record_id, value)

        def update(self, conn, record_id, value):
            return original.update(conn, record_id, value)

    if version == 'v1':
        http_app.OLD = ChangedRead()
    else:
        http_app.NEW = ChangedRead()
    http_app.main()


if __name__ == '__main__':
    main()
