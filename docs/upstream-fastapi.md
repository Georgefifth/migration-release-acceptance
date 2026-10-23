# Public upstream application case

## What this validates
The first reference case used an HTTP app written for our own probes. This case
uses the actual backend from [FastAPI's full-stack template](https://github.com/fastapi/full-stack-fastapi-template),
fixed at `b1125d8839482cb7bbae603ddc6d0081bf87532e`. It exercises real OAuth2
password login, bearer-token authentication, and item create/read/update routes.
It is an integration case based on a public template, not an external team's
installation, an upstream incident, or market validation.

## Candidate change
We introduce a hypothetical application change: v2 maps the API's `title` field
to the physical PostgreSQL column `display_title`. The HTTP contract stays the
same. The original v1 backend still reads and writes `title`.

- Breaking candidate: rename `item.title` directly. Migration and new-app CRUD
  should pass; old, mixed and old-app rollback data requests should fail.
- Compatible candidate: add/backfill `display_title` and synchronize the two
  columns while both app versions are supported. All sixteen probes should pass.
- These are deliberately introduced changes, not defects attributed to upstream.

The same gate and lifecycle checks are reused. The workload provides its own
fixtures, baseline initializer, domain values and provenance. The adapter maps
our numeric probe IDs to UUIDs returned by the real item-create route.

## Reproduce
In a fresh checkout, use Python 3.14 and disposable PostgreSQL 16:

```sh
python -m pip install uv==0.12.5
python -m integrations.prepare_fastapi
uv sync --project .upstream/source --package app --frozen --no-dev
export DATABASE_URL='postgresql://testuser:testpassword@localhost:5432/acceptance'
export ACCEPTANCE_DISPOSABLE_DB=yes
.upstream/source/.venv/bin/python -m integrations.fastapi_case --scenario breaking
.upstream/source/.venv/bin/python -m integrations.fastapi_case --scenario expand
```

These commands verify expected integration outcomes and exit zero only when the
expected verdict is observed. They are harness tests, not release approval.
Each report preserves the actual BLOCK/GO verdict. Reports are in
`reports/upstream/`; generated upstream trees stay in `.upstream/` and are ignored.
The `upstream-fastapi` CI job runs both cases in a clean checkout.
The separate `release-acceptance` job now runs one selected real-app candidate
with release exit semantics. See [release CI integration](ci-integration.md);
the known-outcome verifier commands above remain self-tests.

## Changes and setup cost to record
- One application-model field mapping change and its import in the generated v2
  copy. A pinned original Git blob and exact replacement count detect drift.
- A launcher preserving business/auth routes, adding test readiness and sanitized
  database errors; no auth dependency is replaced.
- A login/item adapter, UUID mapping and baseline initializer using upstream
  SQLModel and user initialization.
- Two candidate SQL fixtures; a new workload configuration reuses the existing
  sixteen operations rather than duplicating the acceptance engine.
- Python 3.14, the upstream locked dependency set, and a disposable DB.

This is more setup than the original example. We have not measured human setup
minutes or demonstrated savings against ordinary upstream CI. Those costs must
be compared with a team's existing tests before claiming easier adoption.

## Evidence and limits
Local integration completed on 2026-10-21 using an isolated Python 3.14.6
virtualenv and disposable PostgreSQL 16.15 container:

- Breaking: BLOCK, 8 PASS / 8 compatibility failures, each SQLSTATE 42703.
- Expand: GO_WITHIN_SCOPE, 16/16 PASS.
- Both runs completed cleanup. A separate query found zero remaining test schemas.
- Original fixture and project-adapter regressions also passed, including partial
  startup failure cleanup. The disposable PostgreSQL container was stopped.
- The first execution caught a launcher bug: the added health route needed a tag
  because the upstream unique-ID generator indexes its first tag. This was fixed
  without changing upstream login or business routes.

Evidence is in `reports/local-upstream/` and
`reports/local-upstream-verification.json`, including actual run IDs and the
hash of the tested source files. These are local working-tree results, not
commit-bound GitLab CI evidence. The case subsequently passed GitLab CI at
commit `7a07317fea5503acf40ee1524f3cff98f6905e54`, pipeline 2980254199,
job 17409532941. Both expected outcomes and cleanup were verified. See
[the demo evidence identities](demo-evidence.json) for exact run IDs. This is a
fixed historical snapshot; later commits need their own checks.

Only the item CRUD workflow is covered. Login provides real authentication, but
password reset, emails, frontend UI, delete, authorization boundaries, concurrent
transactions, lock duration and production deployment are outside these probes.
The disposable job seeds synthetic records and uses ephemeral credentials kept
out of reports. Rollback returns to v1 code without undoing SQL.
