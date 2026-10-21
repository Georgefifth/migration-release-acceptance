# PostgreSQL migration release acceptance

See which application behavior breaks during a schema rollout, with executable
evidence instead of an AI risk score. Working description; public naming is left
to the human participant.

**Status:** runnable reference harness. Two real PostgreSQL fixtures and two
independent synthetic HTTP app processes, with per-request database connections.
Rollback stops both apps and restarts v1 against the migrated schema.
GitLab Duo activation and actual run evidence are tracked in [Duo setup](docs/duo.md).

## The failure this demonstrates
Renaming `customers.email` to `contact_email` passes migration execution and v2
tests, but v1 code still queries `email`. During rollout or app rollback it fails.
The alternative fixture retains both columns and synchronizes reads/writes.

## Run locally (disposable PostgreSQL only)
Use Python 3.12+ and an empty PostgreSQL 16 test database. Never use a production
database. The harness executes trusted repository SQL and creates/removes its own
random schema. Schema isolation is not a sandbox for malicious SQL.

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
export DATABASE_URL='postgresql://testuser:testpassword@localhost:5432/acceptance'
export ACCEPTANCE_DISPOSABLE_DB=yes
.venv/bin/python -m acceptance.demo
.venv/bin/python -m acceptance.runner --scenario expand
.venv/bin/python -m acceptance.runner --scenario breaking
```

The last command intentionally exits **1**. Open `reports/breaking.html`, or use
the equivalent JSON/Markdown. Exit **0** means `GO_WITHIN_SCOPE`; **2** means
`INCONCLUSIVE`. No raw rows, database URLs, or server exception messages are saved.

## GitLab CI
Push a branch or open an MR. Four jobs run:
1. `unit`: guard against unsafe gate/report behavior.
2. `fixture-regressions`: verify that both known fixtures produce the expected
   results. Its green status means the harness works, not that breaking SQL is safe.
3. `adapter-contract`: run the project-local adapter example and verify cleanup
   after a partially started app fails. This is also a harness self-test.
4. `release-acceptance`: checks the pipeline input `migration_scenario` (default
   `expand`). Selecting `breaking` makes the release gate fail. Download reports
   from job artifacts. Inputs are restricted to these two reference fixtures.

## Coverage and limitations
Baseline read/write, migration execution, target-version read/write, old-version
read/write via HTTP, both directions of mixed create/update, and app-process rollback.
All 16 checks, including startup and restart evidence, must pass for a scoped GO.
Interleavings are sequential, not concurrent. No production-scale lock, backfill,
replication or performance claim is made. Rollback does not undo the database.
Passing fixture checks is not a general guarantee of migration safety.

## Documentation
- [Application adapter integration](docs/application-integration.md)
- [Team validation protocol](docs/team-validation.md)
- [Product and acceptance criteria](docs/product.md)
- [Project development rules](AGENTS.md)
- [Duo setup and demo procedure](docs/duo.md)

Original project code is MIT-licensed. Dependencies retain their own licenses;
see [third-party notices](THIRD_PARTY_NOTICES.md).
