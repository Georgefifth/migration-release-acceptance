# Reproduce and record the demo

Status: narration, evidence and walkthrough prepared. No video has been recorded
or submitted. This guide references a fixed verified snapshot, not the latest
branch head. Documentation changes do not move that evidence to another commit.

## Open these before presenting

1. The upstream `comparison.html`, with both candidates visible.
2. The upstream `breaking.html`, ready to select **Failures**.
3. The successful GitLab pipeline and upstream integration job below.
4. The actual historical Duo notes, if showing the optional agent segment.

Use [the narration](demo-script.md). Show the report rather than scrolling through
runner installation logs. Keep the commit/run identity visible when explaining
what was checked. Do not call the green integration self-test a release approval:
it intentionally verifies both a blocked and a compatible candidate.

## Verified evidence snapshot

Evidence commit: `7a07317fea5503acf40ee1524f3cff98f6905e54`.
[Machine-readable identities](demo-evidence.json) record exact run IDs and limits.

| Scene | Evidence |
|---|---|
| Five CI jobs pass; 24 unit tests | [Pipeline 2980254199](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase/-/pipelines/2980254199) |
| Real upstream API, both candidates | [Job 17409532941](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase/-/jobs/17409532941) |
| JSON, HTML, Markdown and comparison | [Upstream report artifacts](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase/-/jobs/17409532941/artifacts/browse/reports/upstream/) |
| Breaking: 8 PASS / 8 FAIL, BLOCK | Run `276923ed-cd61-4ec3-890d-cb6baf0b41a7` |
| Expand: 16/16 PASS, GO_WITHIN_SCOPE | Run `fc3ab6c1-612e-4c72-b890-a059c115c8d5` |
| Historical Duo BLOCK | [MR !2 note 4052241066](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase/-/merge_requests/2#note_4052241066), commit `aaa01d4880269f45129e7dcee85fc72b14111907` |
| Historical Duo GO | [MR !1 note 4059512052](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase/-/merge_requests/1#note_4059512052), commit `215544ba0ceffb8532fdd3e00d342431073405ee` |

The Duo records predate this FastAPI case. They demonstrate the integration, not
agent review of the selected FastAPI snapshot. Do not combine their identifiers
or imply a new session was run. A complete artifact download preserves offline
reports after GitLab's configured 14-day artifact retention expires; the job
links and evidence identities establish where they came from.

## Walkthrough (target 2:30; actual recording duration unmeasured)

| Time | On screen | Action and check |
|---|---|---|
| 0:00 | Upstream comparison | State the old/new overlap problem. Identify synthetic data and the pinned public backend. |
| 0:25 | Breaking full run | Show migration and new-app checks passing; select Failures. Verify eight failures with 42703. |
| 0:55 | Breaking rollback stage | Show restart passing while rollback reads fail. Explain application rollback is not SQL rollback. |
| 1:10 | Upstream comparison | Contrast 8/16 with 16/16 for the same declared operations. Keep source identity visible. |
| 1:40 | Pipeline/job | Distinguish harness self-tests from the selected-scenario release gate. |
| 1:55 | Optional historical Duo note | Read its exact older commit. Explain the agent preserves deterministic evidence and does not merge. |
| 2:15 | Report limitations | State missing concurrency, lock-duration, production and customer validation. |

Do not use the customer-reference SQL example while narrating Item.title:
these are different workloads. The short trial renames customers.email;
the upstream case changes the physical storage for Item.title.

## Hands-on reproduction

For the shorter synthetic reference trial, follow [first trial](first-trial.md).
One command creates both reports and cleans its owned database. A new run has new
run IDs; do not relabel it with the saved CI run IDs.

For the exact upstream source snapshot:

```sh
git clone --branch codex/migration-acceptance-mvp --single-branch https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase.git migration-acceptance
cd migration-acceptance
git switch --detach 7a07317fea5503acf40ee1524f3cff98f6905e54
```

Then follow [upstream reproduction](upstream-fastapi.md) with Python 3.14 and a
user-managed disposable PostgreSQL 16 database. Those manual commands label local
runs local-development unless a verified commit is provided; the saved CI reports
are the commit-bound demonstration. Do not set a CI SHA for edited local code.
The upstream manual setup does not inherit the short trial's Docker cleanup.

To rebuild views from downloaded JSON, from the repository root:

```sh
python3 -m acceptance.report /path/to/breaking.json /path/to/expand.json --output reports/review
```

Open `reports/review/comparison.html`. Both JSON files must come from the same
upstream job/workload. Rendering preserves their verdicts and needs no database.

## Before recording

- Confirm every displayed report's commit, workload and run ID against the table.
- Close credential settings and unrelated tabs; reports contain synthetic data.
- Check that local report links open while disconnected from the internet.
- Rehearse with a timer; shorten narration if the actual take exceeds the limit.
- State that setup savings, team adoption and production safety are unproven.
- Record/export the actual video and verify its playback before calling it done.
  This document and an offline evidence bundle are not a recorded video.
