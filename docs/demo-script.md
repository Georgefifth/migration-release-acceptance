# English demo narration

The recorded offline walkthrough uses English captions and no audio. This script
is an optional spoken version, not a claim that narration was recorded. Evidence
is fixed at `2ec32c7eb316c4f1cedf6e92a27b3e240de55c60` (v0.1.3).
See [recording steps](recording-runbook.md) and [exact identities](demo-evidence.json).

## Problem and actual application

A schema migration and the new application can pass their tests while a rolling
release still breaks old requests. Returning to old code does not restore the old
database schema. Our tool helps PostgreSQL engineers rehearse that overlap before
a human decides whether to release.

This case uses a pinned public FastAPI backend with its real login and Item
create, read and update routes. We deliberately change where Item.title is stored.
This is our test change, not an upstream defect. All data is synthetic.

## Failure, rollback and compatible candidate

The breaking candidate completes migration and new-version checks. Eight old,
mixed-version and rollback reads or writes fail with SQLSTATE 42703: an expected
column is missing. Select Failures to locate those operations. The old process
can restart successfully while its data requests still fail. The result is BLOCK.

The compatible candidate retains and synchronizes both representations during
this transition. All sixteen checks pass. Rollback reads compare the latest
acknowledged committed value, including a valid empty string; any nonempty stale
response is insufficient. The result is GO_WITHIN_SCOPE for these probes only.

## Self-tests and actual release behavior

The comparison uses the two upstream regression runs in job 17412526756. That
job verifies known outcomes and is not a release approval.

The named candidates separately feed the real release job. At the same source
commit, pipeline 2980661072 fails with BLOCK and exit 1, retaining the report;
pipeline 2980660966 passes its compatible candidate. Keep each run ID and pipeline
identity distinct. Offline rendering preserves these saved facts; it does not
execute acceptance again.

## Agent integration and limits

Our manually mentioned GitLab Duo flow reads CI evidence, checks its source/run
identity and posts a bounded explanation. Its verified historical notes belong
to their named older commits. This offline video does not record a live GitLab
session or claim a Duo review of the v0.1.3 snapshot.

The workload is sequential and synthetic. It does not establish concurrency,
production safety or lock duration. Merge and deployment remain human decisions.
Independent customer setup savings and repeated usefulness still require testing.
