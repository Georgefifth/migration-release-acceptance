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

## First trial
With Python 3.12+ and a running Docker installation, use a clean Git checkout and
run one command from the repository root:

```sh
python3 -m acceptance.trial
```

This starts its own disposable PostgreSQL, runs both reference candidates, prints
the report location, and removes the database container and temporary Python
environment. It ignores any existing database connection setting. The first run
downloads dependencies and a database image. No GitLab token is required.
See [the first-trial guide](docs/first-trial.md) for the clone command, expected
results, prerequisite checks, troubleshooting and cleanup after interruption.

## Manual setup (disposable PostgreSQL only)
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

The last command intentionally exits **1**. Open `reports/breaking.html` for
stage-by-stage findings and a failures-only filter. After both runs, open
`reports/comparison.html` to compare matching evidence. These pages work offline
without JavaScript or external assets. You can also use
the equivalent JSON/Markdown. Exit **0** means `GO_WITHIN_SCOPE`; **2** means
`INCONCLUSIVE`. No raw rows, database URLs, or server exception messages are saved.

## Connect a reviewed project

The tool can be installed into your project's test virtualenv from a built wheel.
You do not need to copy your application into this repository. See
[installation and downstream use](docs/installation.md); the package is not
published on PyPI. Installed commands are `migration-accept` and `migration-report`.

Declare your application adapter, synthetic workload, baseline and named candidate
SQL in one reviewed Python configuration. Check it without starting a database:

```sh
python3 -m acceptance.project --integration examples.project_acceptance:integration --check
```

For your own configuration, use the same entry point with `--candidate <name>`
and disposable database settings. A project can declare a single candidate; it
does not need to invent breaking/expand demo files. The command produces the same
sixteen checks and returns 0/1/2 for GO_WITHIN_SCOPE/BLOCK/INCONCLUSIVE. This still
requires application-specific startup and HTTP-operation mapping; it does not
discover or integrate an arbitrary application automatically. See
[the project integration guide](docs/application-integration.md).

## Rebuild a report from saved evidence
No database or application process is needed to review an existing run:

```sh
python -m acceptance.report reports/breaking.json reports/expand.json --output reports/review
```

Open `reports/review/comparison.html`. The command preserves the recorded
verdicts; its successful exit only means files were rendered. Input is checked
before output is written, and two runs of the same candidate are rejected.
Incomplete or mismatched evidence remains explicit in the comparison page.

## GitLab CI
Push a branch or open an MR. Six jobs run:
1. `unit`: guard against unsafe gate/report behavior.
2. `fixture-regressions`: verify that both known fixtures produce the expected
   results. Its green status means the harness works, not that breaking SQL is safe.
3. `adapter-contract`: run the project-local adapter example and verify cleanup
   after a partially started app fails. This is also a harness self-test.
4. `package-contract`: build a wheel, install it into a new virtualenv and run
   a generated downstream project outside the checkout, including blocked/passing
   candidates and database-free report rendering. Synthetic installation evidence.
5. `upstream-fastapi`: exercise actual login and item CRUD in a pinned public
   FastAPI backend, with a reviewed column-mapping change. Integration evidence,
   not real-team adoption or approval of arbitrary migrations.
6. `release-acceptance`: checks the pipeline input `migration_scenario` (default
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
- [Install into your project](docs/installation.md)
- [Iteration plan and release boundaries](docs/iteration-plan.md)
- [Demo walkthrough and verified evidence](docs/recording-runbook.md)
- [English demo narration](docs/demo-script.md)
- [Current product status and remaining questions](docs/project-status.md)
- [Upstream application case](docs/upstream-fastapi.md)
- [Application adapter integration](docs/application-integration.md)
- [Team validation protocol](docs/team-validation.md)
- [Product and acceptance criteria](docs/product.md)
- [Project development rules](AGENTS.md)
- [Duo setup and demo procedure](docs/duo.md)

Original project code is MIT-licensed. Dependencies retain their own licenses;
see [third-party notices](THIRD_PARTY_NOTICES.md).
