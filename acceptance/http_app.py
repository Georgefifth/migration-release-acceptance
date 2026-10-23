"""Synthetic HTTP application fixture. Never expose this server outside test CI."""
import argparse
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .adapters import OLD, NEW


def main():
    import psycopg
    from psycopg import sql

    parser = argparse.ArgumentParser()
    parser.add_argument('--version', choices=['v1', 'v2'], required=True)
    parser.add_argument('--ready-file', type=Path, required=True)
    args = parser.parse_args()
    schema = os.environ['ACCEPTANCE_SCHEMA']
    if os.environ.get('ACCEPTANCE_DISPOSABLE_DB') != 'yes' or not re.fullmatch(
            r'acceptance_[0-9a-f]{32}', schema):
        raise ValueError('Disposable acceptance schema required')
    repository = OLD if args.version == 'v1' else NEW

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Do not log request bodies, rows, or connection strings.

        def reply(self, status, payload):
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def dispatch(self):
            try:
                with psycopg.connect(os.environ['DATABASE_URL'], connect_timeout=5) as conn:
                    conn.execute("SET statement_timeout = '5s'")
                    conn.execute("SET lock_timeout = '2s'")
                    conn.execute(sql.SQL('SET search_path TO {}, pg_catalog').format(
                        sql.Identifier(schema)))
                    if self.path == '/health' and self.command == 'GET':
                        conn.execute('SELECT 1')
                        payload = {'version': args.version, 'pid': os.getpid()}
                    else:
                        match = re.fullmatch(r'/customers/(\d+)', self.path)
                        if not match:
                            self.reply(404, {'error': 'unknown_route'})
                            return
                        customer_id = int(match[1])
                        if self.command == 'GET':
                            payload = {'email': repository.read(conn, customer_id)}
                        else:
                            length = int(self.headers.get('Content-Length', '0'))
                            if not 0 < length <= 4096:
                                raise ValueError('Invalid body size')
                            email = json.loads(self.rfile.read(length))['email']
                            if not isinstance(email, str) or len(email) > 256:
                                raise ValueError('Invalid fixture value')
                            operation = repository.create if self.command == 'POST' else repository.update
                            operation(conn, customer_id, email)
                            payload = {'ok': True}
                # A successful response is sent only after the transaction commits.
                self.reply(200, payload)
            except psycopg.Error as exc:
                self.reply(500, {'error': 'database', 'sqlstate': exc.sqlstate})
            except (ValueError, KeyError, TypeError):
                self.reply(400, {'error': 'invalid_request'})
            except Exception:
                self.reply(500, {'error': 'application'})

        do_GET = dispatch
        do_POST = dispatch
        do_PATCH = dispatch

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    temporary = args.ready_file.with_suffix('.tmp')
    temporary.write_text(json.dumps({'port': server.server_port}))
    temporary.replace(args.ready_file)
    server.serve_forever(poll_interval=0.1)


if __name__ == '__main__':
    main()
