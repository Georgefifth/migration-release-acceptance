# Product specification — HTTP reference milestone

## Audience and problem
Small SaaS teams using PostgreSQL and rolling deployments need evidence that old
application behavior continues to work after a migration. Passing the migration
and new-version tests alone does not establish this.

## Value hypothesis
An MR-scoped compatibility report can reduce manual rehearsal and expose failures
missed by target-schema checks. This is unvalidated: compare against a SQL linter
plus an ordinary CI matrix before investing in a general platform.

## Workflow
1. Developer submits a migration candidate.
2. CI creates a disposable synthetic fixture and verifies v1 behavior.
3. Apply migration, then exercise v2, v1, sequential mixed writes, and v1 return.
4. Produce JSON, Markdown, and a standalone HTML report with exact run/commit IDs.
5. GitLab Duo reads current pipeline evidence, explains the failing operation,
   and recommends a bounded next action. The human decides what to change/merge.

## Deterministic acceptance contract
- `GO_WITHIN_SCOPE` / exit 0: all 16 declared checks pass and cleanup succeeds.
- `BLOCK` / exit 1: baseline and migration pass; compatibility checks fail.
- `INCONCLUSIVE` / exit 2: incomplete evidence, setup, timeout, connection,
  migration, unknown error, or cleanup failure. Never promote this to GO.
- An unsafe rename must pass migration + v2 checks but fail v1/mixed/app rollback.
- An expansion retaining both representations must pass all declared checks.
- Startup/restart failures are INCONCLUSIVE; distinct process IDs are recorded.
- Baseline failure must not be blamed on the candidate migration.
- Every report carries commit, fixture digest, run ID, SQLSTATE, and scope limits.
- Agent text cannot override the deterministic result.

## Reuse and competition
PostgreSQL and psycopg provide execution and transactions. GitLab provides CI,
MRs, artifacts, and Duo. Squawk is a complementary future lint step, not replaced.
Atlas already tests migrations; Reshape supports schema coexistence. The working
hypothesis is easier application-behavior acceptance, not novel migration logic.
Do not copy Time-Traveler or claim isolated migration rehearsal is a new idea.

## Explicit first-milestone limits
Only two trusted reference migrations and two synthetic loopback HTTP application
processes. No arbitrary repository ingestion, application containers, concurrent load,
production snapshots, DB rollback, lock benchmarking, automatic repair or deploy.
The expansion trigger is a fixture-specific example, not a universal recipe.

## Validation before expansion
Ask five relevant teams to compare this workflow against their current CI using
historical incidents. Continue only if at least three want it in a real upcoming
migration and it adds useful coverage or saves meaningful setup/review time.
These are proposed validation criteria, not completed interviews or results.

## Next milestone after evidence
Validate against real teams before supporting user-supplied, reviewed business
applications in the existing CI environment. Do not build a hosted control plane
before validating repeated use and installation effort.
