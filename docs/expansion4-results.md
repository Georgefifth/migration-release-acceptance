# External expansion 4 results — v0.1.7

This cycle's acceptance passed; the continuous test/plan/iterate/test goal remains
active. Overall capability remains partial, not general migration or RLS safety.

The frozen new set contains 24 previously unexecuted contexts: 16 development,
8 holdout, spanning enum values, identity, rules, triggers and row-level security.
All SQL reference probes confirmed the expected semantics. Five PostgreSQL v16
regression files supplied the cases; JSONB was inspected but not tested. Exact
immutable Git tree revision, URLs, hashes, UTC download times and PostgreSQL
license are in reports/validation-expansion4/sources/downloads.json and COPYRIGHT.
Schemas, values, HTTP mapping and oracle probes are evaluator-authored adaptations,
not 24 upstream customer applications.

| Stage | Matching verdict/exit | Interpretation |
| --- | --- | --- |
| v0.1.6 new development | 10/16 | Six original failed classifications retained |
| v0.1.7 same development | 16/16 | Regression after fixes |
| Eight untouched holdout contexts | 8/8 | First execution, no subsequent runtime changes |
| All 39 prior contexts | 39/39 | Regression under a low-privilege role |

Every normal case uses a temporary NOSUPERUSER NOBYPASSRLS role. One explicitly
marked superuser control uses identical FORCE-RLS SQL and intentionally returns
GO: the server bypasses its policy. The normal owner with FORCE sees denied/missing
records and returns BLOCK after repair. Owner-without-FORCE also bypasses policies,
despite false privilege booleans. This proves role conditions affect observations;
it does not constitute a security audit or identify an application's real role.

## Repairs

- Mapped-request 22P02, 428C9 and 42501 now classify as compatibility failures.
  Baseline, candidate execution, startup, unknown errors and cleanup guards remain.
- The reviewed reference server uses a dedicated RecordMissing exception and
  404/error=record_missing response for an explicitly absent expected row. The
  client recognizes only that exact status/marker, or a reviewed adapter's explicit
  semantic reason. Generic 404, unknown route, generic 500, malformed body and
  arbitrary LookupError/IndexError remain unknown. This improves our fixture
  protocol; third-party APIs still require deliberate error mapping.
- SQLSTATE validation now also occurs in ApplicationError itself and requires
  five uppercase ASCII letters/digits. Exception arguments are cleared so direct
  adapter mistakes cannot preserve private text in the exception string.
- Runner-only role capability booleans are recorded without role names. The HTML
  clearly warns if that runner connection can bypass RLS; owner and app-role
  limitations remain explicit. It does not assert that child apps use this role.

Ignored SQL-rule inserts are especially useful: the HTTP server can return success
without the logical row existing. The create is acknowledged, so a real rollback
read must still run; the typed absent-row result yields BLOCK rather than SKIP or
unknown infrastructure failure. This is also exercised through an installed wheel.

## Verification and boundaries

59 unit tests passed on Python 3.12 and 3.14, covering spoofed marker/wrong status,
unknown route, invalid Unicode SQLSTATE and direct exception privacy. Existing
live HTTP lifecycle, acknowledgement-loss/paired-read, rollback-value and injected
cleanup/connection fault suites all passed. The pinned FastAPI login/Item cases
still return 0 for compatible and 1 for breaking SQL. A fresh installed v0.1.7 wheel
passed its console/DB contract, including ignored inserts and offline rebuilding.

All reported runtime schemas and PIDs were independently confirmed removed. Every
owned container and volume was removed, with final owned-schema counts zero.
Browser checks confirmed runner-only warning, zero-failure filtering and 390px
mobile layout (337.6px table, no horizontal overflow or scripts).

The suite still records unmapped hazards: restarted automatic identity sequence
collisions, disabled derived-field triggers, owner/superuser policy bypass and
the older unmapped business invariants. They are not counted as in-scope false GO,
nor hidden as proof of comprehensive safety. Small purposive-context agreement
is not population accuracy or independent adoption evidence.

Full local evidence: reports/validation-expansion4/summary.json, case-results.csv,
frozen.json, holdout-lock.json, per-case reports/logs, role screenshots and wheel
receipt. Original failed run baseline-v016 is separate from repaired-development.
No product runtime changed after opening the eight-case holdout. No new CI,
public deployment, package-index publication or Duo trigger is claimed.

## Next expansion

The next source is ariga/atlas, Apache-2.0, with fixed migration test files already
downloaded into reports/validation-expansion5/sources/. It includes ordinary and
concurrent indexes, index options and transaction-sensitive SQL. These are formatter/
planner test strings, not automatically valid PostgreSQL: independently verify
each selected statement instead of trusting the source's expected plan wholesale.
Freeze the next inputs and expected behavior before execution. Do not treat a
safe INCONCLUSIVE as successful validation of a legitimate unsupported migration.
