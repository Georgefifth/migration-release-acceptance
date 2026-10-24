# Next cycle: explicit migration execution mode

Eight Atlas SQL planner/formatter excerpts were frozen before execution: four
development, four unopened holdout. Source is Apache-2.0 and pinned by immutable
Git tree/file hashes. Independent PostgreSQL probes establish the actual semantics,
not the upstream expected SQL string alone. Synthetic users schema/data/HTTP mapping
remain labeled; this is not execution of Atlas or a customer integration.

## Evidence already observed

v0.1.7 development result: 3/4 task expectations. A valid single-statement
CREATE INDEX CONCURRENTLY succeeds under independent autocommit, but our migration
wrapper raises 25001 and returns INCONCLUSIVE. This is missing execution capability,
not an application incompatibility and not a false approval. The ordinary covering
index and drop work. The BRIN DESC string from the formatter tests is rejected by
PostgreSQL 16 with 0A000, correctly remaining INCONCLUSIVE. No case was relabeled.

## Proposed bounded repair

Expose a reviewed Integration.candidate_transactional boolean, default true.
Pass it through the public project CLI to runner migration execution; only the
candidate step may omit its transaction wrapper. Baseline, application checks and
cleanup behavior remain unchanged. Reject nonboolean configuration without starting
apps or a DB. Report the mode explicitly and include it in evidence comparison
guards. Never infer mode by keyword scanning or implement a SQL parser/engine.

This flag means no outer wrapper, not per-statement autocommit for arbitrary
multi-statement files. PostgreSQL can still group a submitted multi-statement
string in an implicit transaction. Document the single-statement concurrent-DDL
boundary; do not promise generic framework execution or atomic rollback. Unwrapped
partial candidate effects must still lead to safe INCONCLUSIVE on failure and
owned-schema/process cleanup. Trusted SQL may itself control transactions.

The explicit requested mode is already in frozen adapter input, separate from
oracle labels. Updating that reviewed configuration adapter to pass a new public
API is an implementation change, not a changed SQL input or reference answer.

## Acceptance for the next iteration

- Same four development cases must match without changing SQL/labels; the valid
  concurrent create must actually complete before any scoped GO is possible.
- Default remains wrapped. Invalid candidate or requested mode stays safe; no
  lifecycle/cleanup/unknown guard is relaxed and no migration error becomes GO.
- Add meaningful preflight and mode-provenance tests; protect comparison identity.
- Preserve the 63 earlier contexts and unknown/error/privacy/role/acknowledgement
  regressions. Use installed wheel and the real FastAPI reference as appropriate.
- Lock code before opening the four Atlas holdout cases, including concurrent drop,
  partial, operator-class and unique indexes. Report unresolved references honestly
  and do not tune to the holdout. The continuous goal remains active afterwards.
