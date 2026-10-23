# Product status

## Verified snapshot

Evidence source: commit `7a07317fea5503acf40ee1524f3cff98f6905e54`,
[pipeline 2980254199](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase/-/pipelines/2980254199),
verified on 2026-10-23. Later commits require their own CI; these identifiers remain
fixed. Exact upstream runs are in [demo evidence](demo-evidence.json).

## Implemented

- Python acceptance runner, reviewed application/workload adapter boundary, and
  sixteen old/new/mixed-version/application-rollback checks through HTTP.
- Synthetic reference fixtures and a pinned public FastAPI backend using its real
  login and item CRUD routes. A deliberately introduced column-mapping change
  produces eight compatibility failures; the expansion passes all sixteen checks.
- Fail-closed deterministic gate, source/fixture/run identities and cleanup evidence.
- Offline JSON/Markdown/HTML reports, failure filtering and guarded comparison.
- Database-free rendering of saved evidence; invalid or mismatched evidence is
  not silently promoted into a successful comparison.
- A first-trial command that owns its temporary Python environment, labeled Docker
  database, loopback port and report directory. External database settings are ignored.
- Five successful CI jobs and 24 unit tests at the verified snapshot.

A clean public checkout successfully ran the documented trial and produced
commit-bound comparison reports. A second run was interrupted during application
execution: exit 130, no labeled trial containers remained, previous reports were
preserved. The Docker image was cached; no human or cold-download setup-time
benchmark was established. This developer-run check is not customer validation.

GitLab Duo has actual completed reviews on older named commits. The current
FastAPI evidence has not received a new Duo review. See [recording steps](recording-runbook.md)
for exact historical notes; do not describe them as current-head reviews.

## Ready for review

The [first-trial guide](first-trial.md), [English narration](demo-script.md) and
[recording walkthrough](recording-runbook.md) provide a reproducible introduction.
The video has not been recorded or submitted. No MR has been merged or production
system deployed as part of this work.

## Still unvalidated

The current form is a developer CLI and offline results pages. Business integration
requires reviewed fixtures, startup steps and an adapter. There is no independent
interactive setup interface. Human setup/review time, independent team use and
savings versus ordinary CI remain unmeasured.

Next, run the [team validation session](team-validation.md) with consented,
anonymized observations. Learn whether the report changes a real release decision
and whether integration costs less than the team's alternative. Do not substitute
a hosted control plane, more features, or more GitLab setup for this evidence.
