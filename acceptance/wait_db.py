"""Bounded wait for the disposable CI service, without printing its DSN."""
import os
import time
import psycopg

for attempt in range(30):
    try:
        with psycopg.connect(os.environ['DATABASE_URL'], connect_timeout=2) as conn:
            conn.execute('SELECT 1')
        break
    except psycopg.OperationalError:
        if attempt == 29:
            raise SystemExit('Disposable PostgreSQL service unavailable')
        time.sleep(1)
