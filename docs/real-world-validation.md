# External validation — 2026-10-24

**Decision: FAIL under the predeclared exact-classification requirement.**
The product has partial scoped capability. This is not evidence that it falsely
approved an in-scope incompatible case: both remaining failures returned safe
INCONCLUSIVE results instead of the expected BLOCK.

The evaluator froze 21 cases before execution: 16 external SQL cases, one
unsupported pgroll YAML input and four separately labeled synthetic mutations.
There were 16 development cases and five untouched holdout cases. Source material
came from PostgreSQL regression SQL/expected output, Squawk rule tests and pgroll
examples. URLs, immutable Git tree revisions, download times, hashes and license
files are recorded in validation/sources.json and the downloaded evidence.

| Stage | Exact verdict and exit matches |
| --- | --- |
| Original v0.1.4 development | 13/16 |
| Corrected development | 15/16 |
| First untouched holdout run | 4/5 |
| Corrected development + holdout | 19/21 |

The combined 90.5% is case agreement on a small purposive corpus, not population
accuracy. External-SQL-only agreement is 14/16. Known incompatible cases returned
BLOCK in 5/7 cases, INCONCLUSIVE in 2/7, and GO in 0/7. No incompatible case was
deleted or relabeled. Nineteen SQL reference probes were confirmed; two cases
only checked malformed configuration. No skips or unresolved references occurred.

The CHECK/UNIQUE failures expose the same dependency issue: failed creates mean
the later rollback probe reads a nonexistent record; the reviewed synthetic HTTP
mapping reports an unknown error and the conservative gate becomes INCONCLUSIVE.
That mixes an adapter error-mapping limitation and an unconditional dependent
probe. The holdout failure was retained without further tuning. Arbitrary HTTP
errors must not be reclassified as incompatibility to improve these scores.

A separate mapped-payload case passed all 16 checks while an independent write to
an unmapped UNIQUE field failed. GO only covers the declared mapping. Real SQL
plus an evaluator-authored synthetic adapter is not an independent upstream
business-app integration; zero new business applications were integrated here.

Two supported-request SQLSTATE gaps were fixed: 22001 (overlong value) and 23503
(foreign-key violation) now classify as compatibility errors; lifecycle/unknown
guards remain. Original Python 3.14 installation also failed with the old driver
pin. v0.1.5 uses psycopg 3.3.6; a fresh installed wheel passed its actual console
script/HTTP/PostgreSQL contract on Python 3.14. All 53 unit tests passed on Python
3.12 and 3.14. Old and corrected evidence remain separate.

All 19 final runtime schemas and recorded processes were independently confirmed
removed. All three owned PostgreSQL containers and volumes were removed. Median
final CLI wall time was 0.958 seconds, maximum 1.09 seconds; this excludes DB
startup and is not a controlled production or competitor speed result. Maximum
GNU time invocation/child RSS was 45,012 KiB, not total concurrent app+DB memory.

Squawk 2.70.0 saw the same SQL with matching timeout/transaction context. It
flagged rename/drop and the unmapped UNIQUE risk without app execution, and had
no warning for a NOT VALID CHECK that rejected mapped future writes. Static risk
warnings and runtime workflow verdicts are different tasks; no accuracy or speed
winner is claimed. pgroll's YAML was tested only as unsupported input; its engine
was not benchmarked.

Reproduction and evidence layout: [validation/README.md](../validation/README.md).
The local complete report, frozen plan, per-case JSON/HTML/Markdown, CLI logs,
resources and machine-readable summary are in reports/real-world-validation/.
An evidence archive includes the preserved original failures and source patch.

The current video can demonstrate only its selected saved Item cases and report
interactions. It does not substantiate automatic ingestion, general migration
safety, independent customer adoption, concurrency or production readiness.
The public site remains the older published v0.1.4; these fixes and results are
local, not a claimed new GitLab pipeline, deployment or Duo review.
