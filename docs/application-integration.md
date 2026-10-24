# Connect a reviewed application

The project entry point removes the need to write a report/exit-code wrapper.
It does not discover your application automatically. You still provide reviewed
startup, HTTP-operation mapping, synthetic baseline data and candidate SQL.
There is no independent customer installation or measured setup saving yet.

To work from your own repository, first install the wheel into your project's test
virtualenv using [the installation guide](installation.md). Then run
`migration-accept` from your project directory with the same options shown below.
The installed entry point imports only the explicitly named configuration; it
does not search for or automatically execute other project files.

## Check the runnable reference integration

From the repository root, no database or psycopg installation is needed for:

```sh
python3 -m acceptance.project --integration examples.project_acceptance:integration --check
```

This checks the returned configuration, value types, baseline and declared SQL
files without constructing adapters, launching apps or accessing a database.
Since v0.1.2, preflight also binds placeholder arguments to inspectable factory and
initializer signatures. For class factories, it checks declared/inherited
start, stop, read, create and update method signatures and rejects async methods
that the synchronous runner cannot await. It never calls these operations.
It does not execute SQL, verify HTTP endpoints or establish compatibility.
Use --candidate with --check to catch a misspelled candidate before starting a
DB service; an undeclared name exits 2 in both check and run modes:

```sh
migration-accept --integration project_acceptance:integration --candidate title-storage --check
```

A function factory's returned object cannot be inspected without calling it.
Dynamic attributes, descriptors and callables without an inspectable signature
remain runtime checks. A class adapter should declare its protocol methods;
functions may return adapters whose methods are created during construction.
A successful check does not establish correct return values, HTTP routing,
authentication, readiness, cleanup or SQL semantics.

The named Python module is imported and its configuration function is called:
only use code you have reviewed. These imports are not sandboxed.

To run, install requirements.txt and supply your disposable test database through
DATABASE_URL and ACCEPTANCE_DISPOSABLE_DB=yes, as in the manual README setup:

```sh
python3 -m acceptance.project --integration examples.project_acceptance:integration --candidate expand --output reports/project
python3 -m acceptance.project --integration examples.project_acceptance:integration --candidate breaking --output reports/project
```

The second command intentionally exits 1. Reports contain the real verdict;
exit 0 = GO_WITHIN_SCOPE, 1 = BLOCK, 2 = INCONCLUSIVE/setup/configuration failure.
Legacy examples.project_acceptance commands remain available. --scenario is an
alias for --candidate. Neither the project command nor manual setup manages the
lifetime of a database you provide; the first-trial command owns its own database.

## Declare your project's candidate

Keep a reviewed module such as project_acceptance.py importable from the working
directory. The following is a configuration sketch; YourApplication must be
implemented for your application, not copied unchanged from the synthetic app:

```python
from pathlib import Path
from acceptance.integration import Integration
from acceptance.workload import Workload
from your_project.acceptance_adapter import YourApplication

ROOT = Path(__file__).resolve().parent


def integration():
    return Integration(
        application_factory=YourApplication,
        workload=Workload(
            name="your-project-items",
            entity="item",
            fixtures=ROOT / "acceptance_fixtures",
            initial="Existing synthetic item",
            created="Created synthetic item",
            old_write="Old created item",
            new_write="New created item",
            old_update="Old updated item",
            new_update="New updated item",
            application_scope="Reviewed old/new project apps over loopback HTTP; synthetic items only.",
            provenance={"application_revision": "record-the-reviewed-source"},
        ),
        candidates={"title-storage": ROOT / "migrations" / "title-storage.sql"},
    )
```

The workload directory needs baseline.sql, which creates/seeds only synthetic
data in the harness-selected schema. An optional initialize(schema, dsn) callback
can create ORM tables/seed data, as in the real FastAPI case. The baseline read
uses logical ID 1; adapters can map these logical IDs to real UUIDs in memory.
Synthetic values and initializer are configurable without editing the runner.

A project needs only its real declared candidate, not invented breaking/expand
files. Candidate names are lowercase letters, digits, underscores or hyphens,
start with a letter, and have at most 64 characters. Without an explicit mapping,
the reference default looks for breaking.sql and expand.sql beside baseline.sql.
All SQL and initialization code are trusted code; schema isolation is not a sandbox.

Check and run your configuration with the same commands:

```sh
python3 -m acceptance.project --integration project_acceptance:integration --check
python3 -m acceptance.project --integration project_acceptance:integration --candidate title-storage --output reports/title-storage
```

Open reports/title-storage/title-storage.html. Named project candidates have
individual JSON/Markdown links. The existing paired comparison is specifically
for matching breaking/expand reference runs; the tool does not fabricate a
before/after comparison for unrelated project candidates.

## Adapter contract

The factory receives (version, schema, dsn); versions are v1 and v2. Construction
and configuration must not launch processes. The runner registers each adapter
before start so partial startup can be cleaned up.

| Member | Required behavior |
|---|---|
| start() | Launch on loopback, wait for database-aware readiness; return {version, pid, transport: HTTP}. Restart must work after stop. |
| process.pid | The actual owned subprocess; old-app restart must have a different PID. |
| stop() | Stop and wait for owned processes; return true only when stopped. Safe after partial startup and repeated calls. |
| read(conn, id) | Make an HTTP request and return the normalized string value. conn is reserved; do not bypass HTTP with it. |
| create(conn, id, value) | Send HTTP create and wait for the committed result. |
| update(conn, id, value) | Send HTTP update and wait for the committed result. |

Reuse acceptance.http_client.Application for the reference HTTP protocol; override
command(ready_file) with direct argument lists, not shell commands. For different
routes/auth/IDs, implement the mapping in reviewed adapter methods. The FastAPI
case shows actual login, bearer authentication and UUID mapping while preserving
upstream business routes. Filter child environments to the test values required
by the app; do not inherit unrelated CI/developer credentials.

Translate only known incompatibilities into ApplicationError with validated
SQLSTATE, or an assertion on an expected business result. Unclassified HTTP
failures, readiness errors and timeouts remain INCONCLUSIVE. Keep response bodies,
server error text, rows and connection strings out of reports and logs.

The same sixteen checks cover baseline, migration, new/old requests, mixed
creates/updates, restart and old reads of existing/new data. Since v0.1.3 the
restarted old app must return the latest acknowledged update for logical ID 1,
including an empty string; returning any nonempty value is insufficient. An
update that returns committed success sets that expectation even if a subsequent
paired read fails. This supports one
normalized string CRUD workflow, not arbitrary business journeys. Do not claim
coverage for operations you did not map and execute.

Since v0.1.6, JSON schema version 3 records new_write.write_acknowledged separately
from its paired read. If creation did not return committed success, the dependent
rollback_new_data row is SKIP with depends_on=new_write and
reason_code=create_not_acknowledged. It is not a passing rollback read and does
not mean the server definitely did not commit. Unknown acknowledgement loss stays
INCONCLUSIVE. A confirmed create followed by a failed paired read still requires
the real rollback read. The other declared checks continue; known incompatibility
plus this validated skip yields BLOCK, never GO. Baseline/migration/startup,
unclassified errors and cleanup uncertainty retain INCONCLUSIVE. Existing schema
version 2 reports remain readable. Legacy consumers must support the SKIP status
before reading schema version 3 reports.

Reports now state prominently that unmapped fields, derived values and other
business invariants are not checked. A warning does not implement those checks;
this remains one reviewed normalized-string CRUD mapping.

Since v0.1.7, a reviewed adapter may raise ApplicationError(reason='record_missing')
only when it has confirmed absence of an expected logical record. The reference
HTTP protocol recognizes 404 plus error=record_missing; ordinary 404/500 responses
are not automatically migration defects. SQLSTATE is validated even for direct
ApplicationError calls, and exception text is empty. Third-party API adapters
must explicitly map their documented missing-record semantics; do not infer them
from arbitrary response text. Permission/enum/identity errors are observed request
failures, not proof of root cause or a security vulnerability.

Runner-only role-capability metadata omits role names and cannot establish the
application's DB identity. Superusers/BYPASSRLS and ordinary owners without FORCE
can bypass row security; use representative application-role tests before making
any RLS coverage claim.

## Verify through the public FastAPI integration

After completing the pinned-source/dependency steps in
[upstream setup](upstream-fastapi.md), and supplying a disposable database:

```sh
.upstream/source/.venv/bin/python -m acceptance.project --integration integrations.fastapi_case:integration --check
.upstream/source/.venv/bin/python -m acceptance.project --integration integrations.fastapi_case:integration --candidate item-title-storage --output reports/upstream-project
.upstream/source/.venv/bin/python -m acceptance.project --integration integrations.fastapi_case:integration --candidate rename-title --output reports/upstream-project
```

item-title-storage should pass all sixteen checks and exit 0. rename-title should
report BLOCK and exit 1. Unlike the upstream known-outcome self-test command,
this entry point preserves release exit semantics. Different named reports do
not receive the reference-only comparison link.

CI checks preflight, the named passing upstream candidate and both known-outcome
integration cases. Adapter-contract also verifies cleanup after partial startup.
Use your team's existing CI and disposable PostgreSQL service. A checked
configuration is not deployment approval or a successful customer installation.
