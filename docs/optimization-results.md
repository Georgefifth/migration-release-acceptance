# v0.1.6 repair and validation results — 2026-10-24

**Repair acceptance: PASS. Overall product capability: still PARTIAL.**
This iteration repairs observed diagnosis/dependency defects. It does not add
arbitrary business journeys, automatic invariant checks or independent customer
validation. Original failed cases, frozen inputs and expected verdicts remain
unchanged. No source or result was published or deployed in this iteration.

## Plan and implementation

The [preimplementation plan](optimization-plan.md) fixed priorities, acceptance
criteria and safety guards. Six new external SQL cases were frozen before runtime
changes. The original 33 case contexts were reused only as regression evidence.

| Problem | Change | Acceptance evidence |
| --- | --- | --- |
| Known integer/generated overflow became unknown | Mapped-request SQLSTATE 22003 is a compatibility failure | Both prior overflow cases now return BLOCK; valid widened numeric input still passes |
| Failed create caused a meaningless missing-row rollback request | Track new-write acknowledgement independently of its paired read; explicit dependent SKIP | CHECK, UNIQUE and removed-default cases now return BLOCK with the original failures and a real SKIP row |
| Risk of masking actual unknown/cleanup errors | Strict skip identity/parent/acknowledgement validation; original lifecycle guards retained | Unknown create, lost acknowledgement and additional unknown requests remain INCONCLUSIVE; forged skips rejected |
| A committed create might be incorrectly skipped after its read failed | Keep acknowledgement as soon as create returns success | Live HTTP fault regression has failed paired read but PASS for actual rollback_new_data |
| Report could imply skipped checks passed | JSON schema v3, Markdown reason, separate failed/skipped counts and phase state | Reader round-trip and browser phase selection preserve 16 evidence records, including SKIP |
| Static report suggested broader coverage than executed | Prominent coverage statement and machine-readable coverage | Explicitly identifies one normalized string CRUD mapping and untested business invariants |

SKIP means the create was not acknowledged, not that the server definitely did
not commit. It can never produce GO. Only rollback_new_data may use this reason;
its new_write parent must have failed with explicit false acknowledgement.
Unknown parent errors, unrelated unknown checks, lifecycle failures and cleanup
uncertainty remain INCONCLUSIVE. A known incompatibility plus that valid dependent
skip gives BLOCK. No failed case was changed into PASS or deleted.

## Before and after

| Suite | Before this repair | After | Interpretation |
| --- | --- | --- | --- |
| Original 21 contexts, latest prior version | 19/21 | 21/21 | Regression, not unseen evidence |
| Second 12-context challenge set | 9/12 | 12/12 | Regression, not unseen evidence |
| Six new frozen external cases | Not executed before repair | 6/6 on first execution | Untouched holdout, no decision-logic tuning afterwards |

The five prior mismatches now match the same expected BLOCK verdict and exit 1.
All declared GO and setup/migration INCONCLUSIVE cases retain their expected
behavior. There are 39 distinct contexts, not 39 independent production projects.
The corpus includes repeated statements with different inputs and synthetic
baselines/mappings. Agreement here is not a population accuracy estimate.

New holdout cases use previously unexecuted PostgreSQL regression excerpts:
numeric widening with a large write, adding a defaulted column, a positive-only
domain constraint, domain validation over invalid existing data, DROP EXPRESSION
IF EXISTS on a regular column and a forbidden generated-on-generated expression.
Each reference probe was confirmed separately. The two candidate-execution errors
remain INCONCLUSIVE, checking that known error codes do not defeat lifecycle guards.

Sources, immutable versions and hashes remain in validation/sources.json and
validation/round2-sources.json, with original licenses. The new frozen plan records
the exact extraction URL/bytes for every case. These derive from PostgreSQL's
[regression suite](https://github.com/postgres/postgres/tree/REL_16_STABLE/src/test/regress)
and previously acquired Squawk/pgroll test sources. This is external SQL evidence
with evaluator-authored synthetic fixtures, not new upstream application adoption.

## Additional execution checks

- 57 unit tests pass on Python 3.12.3 and 3.14.6.
- Disposable PostgreSQL 16.15 HTTP regressions pass: reference fixtures, project
  adapter/partial-startup cleanup, five exact rollback-value cases, injected
  connection/candidate/baseline/cleanup faults and four new dependency faults.
- The pinned real FastAPI backend's actual login/Item CRUD cases run through the
  public project CLI: item-title-storage exits 0; rename-title exits 1. Its original
  auth/routes remain intact. This is the same reviewed public template integration,
  not an independent team or a new customer workload.
- Python 3.14 fresh noneditable-wheel contract passes, including separate-project
  console scripts, unavailable DB handling and rollback value regressions.
- Independent queries/process checks confirm cleanup for every reported case.
  Each owned corpus container and its volumes were removed; final namespace
  queries found zero owned schemas.

## Browser findings and final-package boundary

First browser QA found Failures (2) incorrectly showing the SKIP as a third row.
The result selector now excludes every non-FAIL status. Mobile QA found the long
skip explanation cramped in the narrow Result column, so it moved to Operation.
The original screenshots are retained. Final checks confirm all eight controls:
16 All rows, 2 Failures, phase counts 3/1/3/2/4/3; native keyboard arrows work.
At 390px viewport the table is 337.6px with no horizontal overflow or scripts.
The skip row height dropped from 232.8px to 162.9px after the layout correction.

These presentation fixes followed the first six-case holdout. Its initial result
is preserved; a subsequent six-case run is explicitly regression, not another
unseen validation. Both wheel contracts passed. The final mobile placement wheel
differs from the last full-contract wheel only in acceptance/report_ui.py and
wheel RECORD; gate/protocol/dependency bytes are identical. Its installed
migration-report entry point was executed from an external working directory,
retaining the input JSON exactly. This boundary is recorded rather than claiming
the first holdout tested the final renderer bytes.

One unit-test fixture initially omitted phase metadata; the assertion was kept
and the fixture corrected. The first isolated core-test invocation also prevented
filtered-environment child processes from importing test modules. Exact reviewed
modules were copied into that owned test directory and the full suite rerun into
a fresh output. Both failed attempts remain in evidence; neither was hidden as a
successful product run.

## Reproduction and artifacts

Use validation/fetch_sources.py and freeze_corpus.py for the first corpus, the
--round2 fetch and freeze_round2.py for the second, then freeze_optimization.py
before another development change. Inputs are immutable after freezing. The
run_corpus --regression option explicitly permits new product code against prior
inputs and records that it is regression evidence. New holdout commands omit it.

Example new holdout invocation after installing requirements and Squawk:

```sh
python3 -m validation.fetch_sources --round2
python3 -m validation.freeze_optimization
reports/validation-env/bin/python -m validation.run_corpus --split holdout --label final-new-holdout --corpus reports/optimization-validation
```

Full local results: reports/optimization-validation/summary.json, frozen.json,
holdout-lock.json, UI receipts/screenshots, wheel verification, unit logs and
runs/final-new-holdout/. Prior-input regression directories are recorded in the
machine summary. The optimization evidence archive includes them without changing
the earlier evidence archives. No final package or website was publicly deployed.

## Remaining product limitations

Unmapped UNIQUE fields and removed generated-expression invariants still escape
the mapped workflow. This repair makes the limitation explicit; it does not
implement missing business checks. Arbitrary authenticated operations, multi-field
invariants, deletes, authorization boundaries, concurrency, lock timing, large
backfills, replication and production approval remain unverified. There is still
no independent team setup-time or adoption evidence. A generally validated
migration-safety claim or broader demo narration would remain unsupported.
