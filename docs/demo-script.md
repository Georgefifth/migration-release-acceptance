# English demo script — working recording draft

Target: approximately 2 minutes 30 seconds at a conversational pace. This is a
script, not a recorded or submitted video. Use the linked verified commits below
until the newer adapter integration has passed its own PostgreSQL CI.

## 0:00 — The release problem

A database migration can pass, and the new application can pass its tests, while
your release still breaks. In a rolling deployment, the old version is still
serving requests. And if you roll back the application, it has to work with the
schema that is already there.

We built a PostgreSQL migration acceptance harness inside GitLab to make that
compatibility visible before someone decides to merge or deploy.

## 0:25 — Show the failing release

Here is an intentionally unsafe migration: rename email to contact_email.
The migration succeeds. The new application starts, reads, and writes successfully.
But those green checks miss the old application.

Our acceptance job also sends real HTTP requests to independent old and new
application processes sharing a disposable PostgreSQL database. It checks reads,
writes, and data exchanged between versions.

The result is BLOCK: eight compatibility checks fail with SQLSTATE 42703, an
undefined column. We also stop both applications and restart the old version.
The restart succeeds, but its requests still fail. Rolling back the application
does not restore compatibility with this schema.

## 1:15 — Show the compatible alternative

The alternative keeps both representations and synchronizes them during the
transition. In this reference example, all sixteen declared checks pass,
including old-version requests and reads after the old process restarts.

The result is GO_WITHIN_SCOPE. It identifies the exact commit, fixture, and run,
and provides the same evidence as JSON, Markdown, and HTML.

## 1:45 — Show GitLab Duo's role

GitLab CI determines the result. Our custom GitLab Duo flow reads the current
merge request and acceptance job, checks that their commit identifiers match,
and posts an explanation with the failed operations and evidence links.

A second component independently rereads the merge request and job log before
publishing. Duo explains the evidence; it does not invent a safety score or merge
the request.

## 2:10 — State the limits and next validation

These are synthetic applications and sequential mixed-version requests. We have
not established concurrent-load behavior or production safety.

Our next question is practical: does this workflow give a small PostgreSQL team
useful coverage with less setup or review effort than its existing CI? We have
prepared an adapter example and a comparison protocol, but real-team adoption is
not yet validated.
