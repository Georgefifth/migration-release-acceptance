# When a run cannot finish

Read the recorded verdict first. BLOCK means the declared compatibility probes
observed an incompatibility after required setup succeeded. INCONCLUSIVE means
the run cannot establish compatibility; it is not proof of a migration defect.
The human remains responsible for deciding what to change and whether to rerun.

The project and reference CLIs print a bounded next-check summary after their
machine-readable report. The same guidance appears in HTML/Markdown reports.
Guidance is derived from recorded phases and failed operations; it does not
change the saved verdict or repair code, SQL or infrastructure automatically.

## Find the failed step

| Report finding | What to check next |
|---|---|
| Adapter setup did not finish | Imports, constructor parameters and required lifecycle/HTTP methods. Construction must not launch processes. |
| Disposable database connection failed | Test service availability and network reachability; verify database name/credentials locally without publishing the URL. |
| Disposable schema setup did not finish | Test connection health and the disposable role's ability to create/remove its own schema. |
| Old-version baseline not established | Baseline SQL, initializer, synthetic ID 1, expected values and old adapter mapping. Do not blame the candidate yet. |
| Candidate SQL did not complete | Recorded SQLSTATE, reviewed candidate, synthetic baseline and PostgreSQL version. Compatibility checks are not established. |
| Old/new app or restart not ready | Reviewed launch command, application dependencies, required test environment, loopback health response and stop/restart behavior. |
| Application execution could not establish compatibility | The actual failed HTTP/auth/ID operation, app health and bounded timeouts. Unknown responses remain INCONCLUSIVE. |
| Declared compatibility failure | Failed operation and SQLSTATE/value assertion; inspect old/new mappings and required overlap behavior. |
| Owned-resource cleanup unconfirmed | Application stop, exact schema state and connection-close evidence; do not treat passing CRUD probes as a scoped GO. |

Startup/request exceptions now retain a failed operation row as well as bounded
error context. This lets a reviewer locate the failed step even if the process
never supplied a complete readiness identity. The tool records exception classes
and validated SQLSTATE, not raw stderr, response bodies, rows or exception text.
To inspect private app diagnostics, use your reviewed launch command in an
isolated synthetic test environment; raw app stderr is not a report artifact.

## Understand cleanup evidence

`cleanup_evidence` records these separate facts:

- `applications_stopped`: whether stop returned confirmed success for all
  registered adapters. An exception/false result cannot count as success.
- `schema_state`: `not_requested`, `present`, `removed` or `unconfirmed`. Completed
  cleanup should be not_requested or removed; present is only an intermediate state.
- `schema`: the fresh `acceptance_<32 hex digits>` identifier owned by this run.
- `connection_closed`: true/false, or null when no connection was returned.

A refused connection before schema creation can have successful owned-resource
cleanup: no schema was requested and all registered adapters were stopped. Its
compatibility verdict is still INCONCLUSIVE because execution did not complete.
A constructor that raises before returning resources cannot establish complete
cleanup; its result stays conservative.

Before issuing CREATE SCHEMA, the runner marks its outcome unconfirmed. If the
request loses its acknowledgement, cleanup still attempts removal of that exact
owned random schema using IF EXISTS. A failed removal remains unconfirmed. No
other schema is targeted, and unknown cleanup is never promoted into GO.

If schema removal is unconfirmed, restore access to the **disposable test DB**,
check the exact recorded schema identity and confirm no test app still uses it
before removing it. Do not delete similarly named schemas or reuse production
data. Old process IDs can be reused by the OS; inspect current ownership before
stopping a process based on saved evidence. A later run uses a new random schema
and does not silently delete a previous run's resources.

If all sixteen operation checks pass but cleanup fails, the result remains
INCONCLUSIVE. The report distinguishes completed execution from unconfirmed
cleanup instead of suggesting that the migration itself failed.

## Rerun and keep evidence separate

Fix the observed setup/adapter/resource issue, then rerun the same named
candidate into a separate output directory if you need to preserve earlier files:

```sh
migration-accept --integration project_acceptance:integration --candidate title-storage --output reports/retry-2
```

Use the new run ID and source identity; rendering an older JSON file does not
rerun acceptance. Older reports without phase/cleanup details get bounded generic
guidance, without inventing which step failed or claiming resources were removed.

## What is actually tested

The adapter-contract CI job includes a real partial HTTP-process startup failure
and injected faults for a reserved non-listening loopback database port, invalid
baseline SQL, invalid candidate SQL, schema-drop failure and connection-close
failure. It also simulates schema creation completing before the caller receives
a usable success result, requiring cleanup of that same owned schema. Each fault
must stay INCONCLUSIVE, produce the appropriate evidence/guidance,
and omit private injected exception text from JSON/Markdown/HTML. The fault harness
repairs only its own deliberately retained test schema and independently queries
for zero leftover test schemas. These are controlled technical regressions, not
production incident or customer-support evidence.
