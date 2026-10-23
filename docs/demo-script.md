# English demo narration

Target: approximately 2 minutes 30 seconds. Rehearse and time the actual take.
This is a prepared script, not a recorded video or a measured presentation time.
Use the FastAPI reports at evidence commit `7a07317fea5503acf40ee1524f3cff98f6905e54`.
See [recording steps](recording-runbook.md) and [evidence identities](demo-evidence.json).

## 0:00 — Problem and audience

A schema migration can succeed, and the new application can pass its tests,
while a rolling release still breaks old application requests. Returning to the
old application may not help, because the database schema has already changed.

We built a PostgreSQL compatibility acceptance tool for engineers who need to
check that overlap before deciding to merge or deploy.

## 0:25 — Show the real API example

This example uses a pinned public FastAPI backend, including its actual login
and item create, read, and update routes. We introduce a hypothetical change:
the new version stores an item's title in a column called display_title.
This is our test change, not a defect reported in the upstream project.

In the breaking candidate, the migration and new-version requests pass.
But the old application still expects the original title column. Eight old,
mixed-version and rollback data checks fail with SQLSTATE 42703: undefined column.

We stop both application processes and restart the old version. Its process
starts successfully, but its requests still fail. The result is BLOCK.

## 1:10 — Show the alternative and the report

The compatible candidate keeps both columns and synchronizes their values during
this transition. All sixteen declared checks pass, including requests after the
old application restarts. The result is GO_WITHIN_SCOPE.

The comparison shows the same operations for both candidates. Open the breaking
run and select Failures to inspect the affected requests. The report retains
the source commit, run identity and limitations. It also works offline.

For a shorter hands-on trial, one command starts its own disposable database,
runs the synthetic reference applications, generates reports and cleans up.
That short trial is separate from this real FastAPI integration.

## 1:55 — Show GitLab and explain Duo

GitLab CI executes the checks and stores the evidence. Our custom Duo flow can
check commit identities and explain acceptance results in the merge request.
These linked Duo notes are actual historical runs on their named older commits;
they are not reviews of the FastAPI results shown here.

## 2:15 — Limits and the next question

The data is synthetic and the requests are sequential. This does not establish
production safety, concurrent behavior or lock duration. No merge or deployment
is automatic. Our next test is whether another team can set it up independently
and gain useful evidence compared with its existing CI.
