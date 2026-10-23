# Product status

## Verified runtime snapshot

Runtime/package evidence: commit `2ec32c7eb316c4f1cedf6e92a27b3e240de55c60`,
v0.1.3, verified on 2026-10-23. [Compatible pipeline 2980660966](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase/-/pipelines/2980660966)
passes all six jobs. [Breaking pipeline 2980661072](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase/-/pipelines/2980661072)
intentionally fails only its release job with BLOCK/exit 1; its other five jobs
pass. [Demo evidence](demo-evidence.json) records distinct regression/release run
IDs. Later documentation/tooling commits do not inherit these runtime results.

## Implemented and verified

- Installed migration-accept and migration-report commands, named reviewed project
  candidates, preflight without app/database startup, and explicit adapter boundary.
- Sixteen old/new/mixed/application-rollback checks through independent HTTP
  processes against disposable PostgreSQL. Real pinned FastAPI login/Item routes.
- Exact rollback values: stale/corrupt nonempty data is blocked; legitimate empty
  strings pass. A failed paired read does not erase an acknowledged committed write.
- Deterministic release exits, bounded failure guidance, source/run/fixture identity,
  separate process/schema/connection cleanup evidence and offline reports.
- 48 unit tests; fixture, adapter/fault, installed-wheel and upstream CI jobs pass.
  Five real HTTP rollback-value cases pass both from source and the installed wheel.
- A first-trial command owning its temporary environment, labeled Docker database,
  loopback port and report directory; external database settings are ignored.

The earlier developer-run clean-checkout/interruption trial remains historical
technical evidence, not a new v0.1.3 user setup-time measurement. The installed
wheel contract is generated and synthetic, not an independent customer project.

## Demonstration

The [recording runbook](recording-runbook.md), [English script](demo-script.md) and
[evidence identities](demo-evidence.json) describe the fixed v0.1.3 snapshot.
A local captioned silent offline-report walkthrough is recorded separately from
live GitLab/Duo execution. Its exact file identity and verification status are
recorded in the evidence manifest. It has not been published to YouTube or submitted.

Duo has actual completed evidence reviews on older named commits. There is no
current v0.1.3 Duo review in this snapshot; historical notes must not be relabeled.
No MR is merged, package published to an index or production system deployed.

## Remaining validation and delivery

The product is a developer CLI with offline results. Startup/auth/HTTP mapping,
fixtures and workload still require reviewed integration code. Independent team
setup, repeated usefulness and savings versus ordinary CI remain unmeasured.
Use the [team validation session](team-validation.md) when a participant is
available; the user currently has none.

For a complete hackathon presentation, capture an explicitly authorized current
Duo review and automation sequence, verify the final video, obtain a public
YouTube link and complete the submission with the human. The current local clip
shows real report behavior, not the entire agent execution. Do not add a hosted
control plane or features in place of missing evidence.
