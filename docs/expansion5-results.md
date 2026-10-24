# Real-world validation: explicit candidate execution mode (v0.1.8)

Cycle acceptance: **PASS**. Overall product capability: **PARTIAL**.
The continuous external-test/plan/iterate/test goal remains active. These results
support the declared synthetic compatibility probes, not production migration safety.

## Scope and predeclared plan

The product runs a reviewed SQL candidate between independent old/new HTTP apps,
then exercises 16 declared CRUD/lifecycle/rollback checks. Target users are teams
wanting evidence about those specific old/new mappings before schema rollout.
Inputs are reviewed Python Integration/Workload declarations and UTF-8 SQL; outputs
are JSON, offline Markdown/HTML, and exit 0/1/2 for GO_WITHIN_SCOPE/BLOCK/INCONCLUSIVE.
It is not a SQL parser, framework runner, production deployer or general safety scan.

The plan in `docs/expansion5-plan.md` was committed before implementation. Eight
external SQL contexts were frozen before the baseline run: four development and
four holdout. All eight are labeled Advanced index-DDL contexts; diversity comes
from concurrent create/drop, covering, partial, unique and BRIN operator-class or
invalid ordering syntax, not from eight independent applications. Schemas, values,
HTTP mappings and direct-reference queries are evaluator-authored synthetic setup.
No downloaded Go code, scripts or Atlas binary were executed.

## Source and ground truth

- [Atlas PostgreSQL SQL planner/formatter tests](https://github.com/ariga/atlas/blob/ed994a77898e48377f9a9c391f2d1c49f5703b8d/sql/postgres/migrate_test.go)
  supplied the eight selected SQL strings.
- [Atlas integration tests](https://github.com/ariga/atlas/blob/ed994a77898e48377f9a9c391f2d1c49f5703b8d/internal/integration/postgres_test.go),
  [initial migration](https://github.com/ariga/atlas/blob/ed994a77898e48377f9a9c391f2d1c49f5703b8d/internal/integration/testdata/migrations/postgres/1_initial.sql),
  and [trigger fixture](https://github.com/ariga/atlas/blob/ed994a77898e48377f9a9c391f2d1c49f5703b8d/sql/migrate/testdata/lexgroup/1_trigger.sql)
  were inspected/downloaded but are not additional scored cases.
- [Atlas Apache-2.0 license](https://github.com/ariga/atlas/blob/ed994a77898e48377f9a9c391f2d1c49f5703b8d/LICENSE)
  is retained. Public access requires no account. Immutable Git tree revision,
  complete URLs, UTC download time, byte counts and SHA-256 for every file are in
  `reports/validation-expansion5/sources/downloads.json`.
- [PostgreSQL 16 CREATE INDEX](https://www.postgresql.org/docs/16/sql-createindex.html)
  documents that concurrent creation cannot run inside a transaction block.

Upstream expected formatter strings are **not** ground truth. An independent
PostgreSQL connection executes each selected candidate with its reference query.
It confirmed all eight semantics, including rejection of BRIN DESC with 0A000.
That string's presence in a formatter test is not evidence of an Atlas engine bug.
The oracle/labels are outside product inputs; the adapter reads only mapping,
synthetic values, reviewed SQL and explicitly requested transaction mode.

## Baseline, change and retest

| Stage | Matching expected verdict and exit | Meaning |
| --- | --- | --- |
| Original v0.1.7 development | 3/4 | Original failure preserved |
| v0.1.8 same development | 4/4 | Repaired known cases; not independent evidence |
| First execution of locked holdout | 4/4 | New contexts, no subsequent runtime changes |
| Prior unchanged contexts | 63/63 | Regression; 61 SQL references and 2 configuration cases |

The original concurrent-create case returned INCONCLUSIVE/25001 despite a valid
single statement: every candidate was forced into the runner transaction. This
was a missing execution capability, not misclassification of an application error
and not a false approval. It now completes its migration and all 16 HTTP checks.

`Integration.candidate_transactional=False` explicitly omits only the candidate's
outer transaction; the default remains True. Preflight/direct runner reject
nonbooleans before constructing apps or connecting. No keyword guessing or SQL
splitting was added. JSON, Markdown and HTML record the mode, and comparison rejects
differing modes. Historical reports default to the original wrapped mode.

The BRIN DESC case still returns INCONCLUSIVE/0A000. Installed-wheel negative tests
confirm concurrent SQL under the default wrapper remains INCONCLUSIVE/25001, as
does a multi-statement string containing concurrent SQL even without the wrapper.
Omitting the outer transaction is not a generic per-statement migration engine or
an automatic SQL rollback mechanism.

## Environment and reproducibility

PostgreSQL 16.15, official `postgres:16-alpine` image SHA-256
`721873c34ceb9f8d8fc265984940dc982404c105f19ad51be9fdc5970a6080ea`;
Python 3.12.3 / 3.14.6 and psycopg 3.3.6. Each evaluator run uses an owned disposable
Docker container (512 MiB, one CPU, 128 PIDs), loopback-only port and synthetic data.
The normal role is NOSUPERUSER NOBYPASSRLS; a preserved older superuser-control case
is explicitly labeled. Credentials and row values are not evidence artifacts.

From this project, with the reviewed environment prepared:

```sh
.validation-venv312/bin/python -m unittest discover -s tests -v
.validation-venv/bin/python -m unittest discover -s tests -v
.validation-venv312/bin/python -m validation.run_corpus \
  --corpus reports/validation-expansion5 --split development \
  --label fresh-development-label --least-privilege --core-checks
.validation-venv312/bin/python -m validation.run_corpus \
  --corpus reports/validation-expansion5 --split holdout \
  --label fresh-holdout-replay-label --least-privilege
```

A holdout replay is a regression, not another independent first run. Input hashes,
original labels and initial failed artifacts stay unchanged. `holdout-lock.json`
binds the runtime, adapter, dependency and package metadata before first holdout;
all hashes still match afterwards. Raw runs are under `runs/`, older-regression
copies/results under `legacy63/`. Do not regenerate frozen corpora over originals.

## Additional verification and performance

- 62 unit tests pass on each Python version, including invalid modes, no-invocation
  preflight, public-CLI passthrough, report persistence and comparison isolation.
- Live reference, adapter startup/cleanup, exact rollback values, injected faults
  and acknowledgement/dependency tests pass; no gate safeguards were relaxed.
- The fresh noneditable v0.1.8 wheel passes from a separate generated project with
  no checkout on PYTHONPATH. It exercises concurrent-mode positive and negative
  cases, missing-record semantics, unavailable DB, offline rendering and rollback.
- Pinned real FastAPI auth/Item integration returns 0 for compatible storage and
  1 for rename. This is a public upstream reference, not customer adoption.
- Browser verification confirms the HTML exposes `Candidate transaction wrapper:
  disabled`, 16 rows, explicit limitations and zero scripts. Screenshot and DOM
  observations are saved; this was local validation, not a public deployment.
- Every evaluated run independently confirms owned schemas absent and recorded
  application PIDs no longer live. All owned containers/volumes are removed.

Per-step wall time, CPU and peak RSS plus container memory observations remain in
raw JSON/logs. Concurrent-create product execution was 0.31 s before (early failure)
and 0.84 s after (all checks completed), about 42 MiB recorded peak RSS in each.
These are different workloads and **not a speed improvement claim**. Tiny synthetic
schemas and single runs cannot establish production performance or tail latency.

## Competitor boundary and capability decision

Squawk 2.70.0 static warnings were preserved for the same SQL. The existing evaluator
assumes a transaction in Squawk even for our new unwrapped cases; those warnings
are not a matched-mode benchmark and must not support a superiority claim. Static
SQL risk linting and app compatibility execution answer different questions. Atlas
was a licensed source of statements; its engine was not benchmarked. No fair
cross-product accuracy or speed ranking has been established.

All four new holdout cases expect scoped GO; 4/4 is task-expectation agreement, not
an estimate of incompatibility recall. The wider 63-case result is a regression,
not independent generalization. Older unmapped generated-field, identity and RLS
hazards still demonstrate scope gaps. No samples were removed or relabeled.

Supported demo claim: explicitly configured single-statement concurrent index DDL
can execute before the declared old/new CRUD/rollback probes, with bounded evidence.
Unsupported claims: production-safe migrations, large-table locking/performance,
concurrent application traffic, arbitrary migration-framework semantics, full RLS
security, or verification of unmapped business invariants. Therefore overall
capability stays PARTIAL despite this cycle passing its predeclared acceptance.

Machine summary: `reports/validation-expansion5/summary.json`; all-stage rows:
`results.csv`; full original/repaired/holdout JSON/HTML/logs and source manifests
remain in that directory. Build failures caused by missing pip/restricted cache or
network are retained alongside the successful uv wheel build, not hidden.
