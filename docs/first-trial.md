# Your first trial

The reference trial demonstrates one specific failure: a column rename can pass
migration execution and new-version tests while old application requests fail.
The compatible candidate retains both columns while both versions are supported.
This is a synthetic example, not validation of your application's migration.

## Prerequisites

- Linux or macOS, or a Linux environment in WSL.
- Python 3.12 or newer, including `venv` and pip support.
- Docker installed, running, and accessible to your current user.
- Network access to this public GitLab repository, your configured Python package
  index, and Docker Hub. The first run downloads Python dependencies and the
  official `postgres:16-alpine` image. No paid service or GitLab token is needed.

From a terminal, obtain a clean checkout of the current MVP branch:

```sh
git clone --branch codex/migration-acceptance-mvp --single-branch https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase.git migration-acceptance
cd migration-acceptance
python3 -m acceptance.trial
```

Optional prerequisite check: `python3 -m acceptance.trial --check`. It checks
Docker access and the Python venv entry point without creating resources; it does
not verify downloads, disk capacity or a complete environment installation.

## What happens

The command creates a temporary Python environment, installs the declared
dependency, starts its own PostgreSQL container on a random **127.0.0.1** port,
and runs both reference candidates through independent old/new HTTP applications.
An existing `DATABASE_URL` is ignored. No existing database is contacted.

Each invocation writes to a new `reports/trial-<id>/` directory, preserving
previous reports. The terminal prints its absolute path. Open `comparison.html`
in your browser; no web server, account or internet connection is needed to view
the saved report. Select **Open full run**, then **Failures** to inspect the
failing application operations and SQLSTATE.

Expected evidence:

| Candidate | Migration/new app | Old, mixed and rollback data requests | Verdict |
|---|---|---|---|
| Breaking rename | Pass | Eight failures, SQLSTATE 42703 | BLOCK |
| Expand/backfill/synchronize | Pass | Pass | GO_WITHIN_SCOPE (16/16) |

Both candidates must complete application/schema cleanup. The trial exits 0
only when its expected fixture assertions pass and its container is removed.
That exit status means the demonstration worked; it does not approve a release.
Setup, unexpected outcomes or unconfirmed container cleanup exit 2. Ctrl+C exits
130 if cleanup succeeds.

The trial identifies a clean checkout's real Git commit automatically. Edited or
unversioned source is labeled `local-development`; individual findings remain
available, but the report withholds direct candidate comparison. Commit reviewed
changes or use a fresh checkout instead of inventing a commit identifier.

## Cleanup and troubleshooting

Normal completion and interruption remove the trial's labeled database container
and its anonymous data volume, and remove the temporary Python environment.
Reports and downloaded Docker images remain. The command does not run sudo,
change Docker/network settings, delete other containers, or prune Docker storage.

If Docker becomes unavailable during cleanup, the terminal prints the unique
container name and a targeted removal command. Restore Docker access, then run
that exact command. After a machine crash or SIGKILL, list owned resources with
`docker ps -a --filter label=acceptance.trial`; inspect the names and remove only
the trial containers with `docker rm --force --volumes <container-name>`.

| Message | Next action |
|---|---|
| Docker missing/unavailable | Install or start Docker and check user access; rerun `--check`. |
| Could not create Python environment | Install your Python distribution's venv/pip support. |
| Dependency download failed | Check access to your configured Python package index. |
| Could not start PostgreSQL | Check Docker Hub connectivity, available disk/memory and Docker status. |
| Database did not become ready | Check Docker resources; retry after cleanup completes. |
| Expected outcomes not verified | Inspect any retained JSON/HTML evidence; do not treat this as a successful trial. |
| Direct comparison withheld | Use a clean checkout of the same source for both runs. |

The original manual setup remains available in the README for users who already
manage a disposable PostgreSQL database. For the real public FastAPI backend case,
see [upstream integration](upstream-fastapi.md); this shorter trial uses the
synthetic reference HTTP applications and does not install the upstream backend.

## Trial acceptance checklist

Without editing code or supplying database credentials, a first-time user should
be able to produce both expected outcomes, locate the report, identify why old
requests failed, and confirm container cleanup. Record setup duration and any
point requiring help; no human setup-time claim has been measured yet.
