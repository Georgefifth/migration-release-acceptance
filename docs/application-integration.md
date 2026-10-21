# Connect a reviewed application adapter

This is a small project-local extension point, not automatic application discovery.
The runnable example still uses our synthetic customer app. It proves the wiring;
it is not evidence of a real team's installation, adoption, or time saved.

## Try the integration example
With the same disposable database settings as the README:

```sh
python -m examples.project_acceptance --scenario expand
python -m examples.project_acceptance --scenario breaking
python -m examples.verify_adapter
```

Expand must exit 0; breaking must exit 1. Reports go to
`reports/project-adapter/`. The verifier also simulates a startup failure after a
real HTTP process has started: it requires INCONCLUSIVE and successful cleanup.
This is a harness self-test, not a release gate. CI runs it as `adapter-contract`.

## Adapter boundary
Call `run(scenario, dsn, application_factory=YourApplication)` from reviewed code.
The factory receives `(version, schema, dsn)`; versions are `v1` and `v2`.
Construction must not launch processes. The harness registers adapters for cleanup
before calling `start`, including if startup fails partway through.

| Member | Contract |
|---|---|
| `start()` | Launch and wait for readiness; return `{version, pid, transport: 'HTTP'}`. A stopped adapter must be restartable. |
| `process.pid` | Actual subprocess PID; restart must produce a different PID. |
| `stop()` | Stop and wait for owned processes; return true only once stopped. Safe to call repeatedly and after partial startup. |
| `read(conn, id)` | Send an HTTP request and return the normalized email string. `conn` is reserved; do not bypass HTTP with it. |
| `create(conn, id, email)` | Send an HTTP create request and wait until it commits. |
| `update(conn, id, email)` | Send an HTTP update request and wait until it commits. |

Reuse `Application` if your test app follows the reference protocol. Override
`command(ready_file)` with an argument list for reviewed v1/v2 launch commands;
commands execute directly without a shell. The child receives `DATABASE_URL` and
`ACCEPTANCE_SCHEMA` through its environment. It binds only to loopback and writes
`{"port": actual_port}` atomically to `ready_file` once listening. `GET /health`
must query the database and return `{version, pid}`. Customer endpoints are
`GET /customers/:id`, `POST /customers/:id`, and `PATCH /customers/:id`; writes
accept `{"email": "synthetic-value"}`, and reads return `{"email": "..."}`.

Apps with other protocols need their own reviewed adapter. Translate only known
business incompatibilities into `ApplicationError` with a verified SQLSTATE, or
an assertion on an expected business result. Unknown server errors, timeouts and
unclassified HTTP failures must remain INCONCLUSIVE. Never expose raw response
bodies or server error strings in reports. Do not change errors into success.

## What still needs editing for a real business application
The fixture and probes currently assume the customer/email example and its known
record IDs and expected values. A factory alone does not make the harness support
arbitrary business workflows. Adapt the reviewed fixtures and probes together;
keep baseline, both versions, both directions of mixed writes, rollback and
cleanup evidence. Update the required check set and regression cases when the
workflow changes. Never preserve the old checks while claiming new coverage.

Use the existing team's CI and disposable PostgreSQL service. Do not import
production data, connect a production database, ingest untrusted adapter code, or
run uploaded code in a shared service. Schema isolation is not a SQL sandbox.
Inspect child-process behavior and inherited CI variables before integrating a
new app. Avoid secrets in the disposable CI job.
