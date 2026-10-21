# Product status

## Current product form
A developer tool: Python acceptance runner, reviewed application adapters, and
JSON/Markdown/HTML reports. GitLab CI runs the tool; Duo explains its evidence.
The product's core is the application compatibility check, not GitLab setup.

## Implemented and previously verified
At commit `215544ba0ceffb8532fdd3e00d342431073405ee`, pipeline 2972546755:
- Ten gate, report, HTTP error-boundary and cleanup unit tests pass.
- Synthetic v1/v2 HTTP app acceptance: sixteen declared checks pass for expand.
- Unsafe rename is blocked by the fixture regressions.
- A project-local adapter runs both candidates; partial startup failure is
  INCONCLUSIVE and cleans its process/schema.
- Duo independently reads current-head evidence and posts a scoped report.

The core implementation lives in `acceptance/runner.py`, `http_client.py`,
`http_app.py`, `report.py` and the SQL fixtures. These are executable source code,
not just a pipeline configuration. `examples/project_acceptance.py` demonstrates
the reviewed adapter boundary.

## Locally integration-verified public application case
The FastAPI upstream case adds a pinned public backend, real login/item routes,
a derived v2 column mapping, business-specific fixture initialization and an
adapter for the real API. Local PostgreSQL/API integration passed on 2026-10-21: the breaking candidate
produced 8 compatibility failures and BLOCK; the expansion passed all sixteen
checks. The original fixture/adapter regressions also pass. Remote CI for these
working-tree changes is still pending; this is not real-team adoption evidence.

## Product experience still to establish
The current report is a results page; configuration is still performed in code.
There is no independent interactive setup interface. We have not established
that adapter setup is faster or clearer than a team's existing CI tests.

The next product decision should come from one actual business integration and
team feedback: which setup steps can be removed, which missing checks matter,
and whether the report changes a release decision. Avoid adding a hosted
control plane or more GitLab configuration to substitute for that evidence.
