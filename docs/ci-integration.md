# Use application evidence in the release check

A green known-outcome verifier means the test harness behaved as expected. It
can intentionally run a breaking migration, observe BLOCK, and still exit zero.
That command must not be used as a release gate.

The `release-acceptance` job now runs the real pinned FastAPI integration through
the project command. It has a fresh disposable PostgreSQL service and prepares
the same locked upstream app as the integration self-test. It does not reuse the
self-test's success status, database or report as its own release verdict.

## Select a candidate in this repository

Run a pipeline on the reviewed branch/commit with the `migration_scenario` input:

| Input | Actual project candidate | Expected release job |
|---|---|---|
| expand (default) | item-title-storage | 16/16 pass, GO_WITHIN_SCOPE, exit 0 |
| breaking | rename-title | 8 pass / 8 compatibility failures (42703), BLOCK, exit 1 |

The public FastAPI backend uses its real OAuth2 login and item create/read/update
routes. The title-column mapping is our deliberately introduced change, not an
upstream defect. All data is synthetic. Scope remains sequential probes, without
production, concurrent-load, lock-duration or large-backfill assurance.

The `integrations.release_acceptance` wrapper only validates the existing input
and maps it to a reviewed named candidate. It delegates to acceptance.project and
returns its exact 0/1/2 status. It never converts an expected BLOCK into success.
Configuration/setup/execution or cleanup uncertainty remains exit 2.

With dependencies/source and a disposable DB already prepared as in
[upstream setup](upstream-fastapi.md), the exact job command is reproducible:

```sh
.upstream/source/.venv/bin/python -m integrations.release_acceptance --scenario expand
.upstream/source/.venv/bin/python -m integrations.release_acceptance --scenario breaking
```

The second command intentionally exits 1. Reports are in reports/release/, named
item-title-storage or rename-title. Job artifacts use `when: always`, so the
blocked report remains downloadable after the job fails. Do not replace a failed
release report with a green self-test report.

## Verify both outcomes without changing source

Run the default MR pipeline for expand, then create an API/manual pipeline at
the same source commit with migration_scenario=breaking. Confirm all of:

1. Both pipelines and both release-report commits match the intended source SHA.
2. The passing report identifies fastapi-upstream-items and item-title-storage,
   with sixteen passing checks, completed execution and confirmed cleanup.
3. The blocked report identifies rename-title, with migration/new-app checks
   passing but eight old/mixed/rollback data operations failing with 42703.
4. The blocked release job fails with exit 1 even though the known-outcome
   self-test jobs succeeded. INCONCLUSIVE/exit 2 is not an acceptable substitute
   for this deliberately demonstrated BLOCK.
5. Both reports preserve real source/fixture/run identities and scope limits.

GitLab's [pipeline API](https://docs.gitlab.com/api/pipelines/) accepts an inputs
hash, for example `{"migration_scenario": "breaking"}`. Use the selected branch
and independently check the returned SHA; it may advance between API requests.
The UI can also set the same validated input. No trigger token is required when
using an already authorized pipeline API connection.

The failing pipeline is deliberate verification evidence. It does not change
source or repair SQL. A later successful pipeline must still name its candidate
and SHA; never infer compatibility from whichever green badge is most convenient.

## Use the blocking command in your own project's CI

Keep your existing project environment/dependency setup and disposable PostgreSQL
service. Install the reviewed tool wheel into that test environment using
[installation](installation.md), and declare your reviewed integration and named
SQL as in [project integration](application-integration.md).

After that setup, the acceptance job's blocking step is simply:

```yaml
application-acceptance:
  stage: test
  # Supply your existing app/test environment, disposable DB and reviewed wheel.
  script:
    - migration-accept --integration project_acceptance:integration --candidate title-storage --output reports/acceptance
  allow_failure: false
  artifacts:
    when: always
    paths: [reports/acceptance/]
```

The snippet is the blocking step, not a complete application-specific setup.
Provide DATABASE_URL and ACCEPTANCE_DISPOSABLE_DB=yes for the disposable test
service. Keep candidate/configuration selection in reviewed repository code or
validated inputs, rather than taking launch commands or SQL from MR comments.

Do not append `|| true`, mark the job optional, or call the known-outcome demo
verifier instead. Preserve exit 1 and 2 as failures in your workflow. This job
does not configure protected branches, enforce every possible merge route or
deploy anything; owners still control GitLab merge/deployment policy.

Duo can read the actual release report using its existing job/marker protocol.
Historical agent notes remain tied to their older commits until a new session
actually reviews current-head evidence; changing this CI job is not that review.
