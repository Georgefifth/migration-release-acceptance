"""Launch the upstream application, with isolated DB scope and sanitized errors."""
import argparse
import json
import os
import socket
import sys
import threading
import traceback
import time
import uuid
from pathlib import Path

SEED_ID = '00000000-0000-0000-0000-000000000001'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['initialize', 'serve'], required=True)
    parser.add_argument('--version', choices=['v1', 'v2'], default='v1')
    parser.add_argument('--ready-file', type=Path)
    args = parser.parse_args()
    if os.environ.get('ACCEPTANCE_DISPOSABLE_DB') != 'yes':
        raise ValueError('Disposable DB required')
    # Resolve upstream's relative .env against its own downloaded backend only.
    os.chdir(Path(__file__).resolve().parent.parent / '.upstream/source/backend')
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / '.upstream' / args.version))
    from sqlmodel import Session, SQLModel, select
    from app.core.config import settings
    from app.core.db import engine, init_db
    from app.models import Item, User

    if args.mode == 'initialize':
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session:
            init_db(session)
            user = session.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).one()
            session.add(Item(id=uuid.UUID(SEED_ID), title='Existing project item', owner_id=user.id))
            session.commit()
        return

    from app.main import app
    from fastapi.responses import JSONResponse
    from sqlalchemy import text
    from sqlalchemy.exc import SQLAlchemyError
    import uvicorn

    @app.get('/__acceptance/health', include_in_schema=False, tags=['acceptance-test'])
    def health():
        with engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        return dict(version=args.version, pid=os.getpid())

    # The upstream frontend is mounted at '/'. Keep only the test health route
    # ahead of that mount; upstream auth and business routes are unchanged.
    app.router.routes.insert(0, app.router.routes.pop())

    @app.exception_handler(SQLAlchemyError)
    async def database_error(_request, exc):
        # Test-only error visibility. No auth bypass, row text or raw exceptions.
        state = getattr(getattr(exc, 'orig', None), 'sqlstate', None)
        if not isinstance(state, str) or len(state) != 5 or not state.isalnum():
            state = None
        return JSONResponse(status_code=500, content={'error': 'database', 'sqlstate': state})

    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen(128)

    server = uvicorn.Server(uvicorn.Config(app, log_level='critical', access_log=False))

    def ready():
        while not server.started:
            time.sleep(0.01)
        temporary = args.ready_file.with_suffix('.tmp')
        temporary.write_text(json.dumps({'port': listener.getsockname()[1]}))
        temporary.replace(args.ready_file)

    threading.Thread(target=ready, daemon=True).start()
    server.run(sockets=[listener])


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Diagnostics contain locations/types only, never exception text or rows.
        destination = Path(__file__).resolve().parent.parent / 'reports/upstream'
        destination.mkdir(parents=True, exist_ok=True)
        diagnostic = {'kind': type(exc).__name__, 'attribute': getattr(exc, 'name', None),
                      'frames': [{'file': Path(f.filename).name, 'line': f.lineno, 'function': f.name}
                                 for f in traceback.extract_tb(exc.__traceback__)]}
        (destination / 'startup-diagnostic.json').write_text(json.dumps(diagnostic, indent=2)+'\n')
        raise SystemExit(1)

