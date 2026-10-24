# Migration acceptance: BLOCK

Scenario: `rename-title` · Run: `ff2362fa-c0da-4bf8-b949-e3e995104eef`

Commit: `2ec32c7eb316c4f1cedf6e92a27b3e240de55c60`

Transport: HTTP

Workload: fastapi-upstream-items

Fixture SHA-256: `3cf598c14f3b744723e71c3e2896a24b370373192d89db147df166b0162fb55c`

Candidate transaction wrapper: enabled

| Stage | App | Operation | Result | SQLSTATE |
|---|---|---|---|---|
| baseline | v1 | Start independent old HTTP application | PASS | — |
| baseline | v1 | Read existing project item | PASS | — |
| baseline | v1 | Create and read project item | PASS | — |
| migration | - | Apply candidate SQL | PASS | — |
| target | v2 | Start independent new HTTP application | PASS | — |
| target | v2 | Read migrated project item | PASS | — |
| target | v2 | Create and read project item | PASS | — |
| rollout | v1 | Read migrated project item | FAIL | 42703 |
| rollout | v1 | Create and read project item | FAIL | 42703 |
| mixed | v1 → v2 | Old creates; new reads | FAIL | 42703 |
| mixed | v2 → v1 | New creates; old reads | FAIL | 42703 |
| mixed | v2 → v1 | New updates; old reads | FAIL | 42703 |
| mixed | v1 → v2 | Old updates; new reads | FAIL | 42703 |
| app_rollback | v1 | Stop both apps; restart v1; verify new process identity | PASS | — |
| app_rollback | v1 | Read latest acknowledged value after rollout | FAIL | 42703 |
| app_rollback | v1 | Read data committed by v2 | FAIL | 42703 |

Upstream provenance: `{"change": "v2 Item.title maps to physical column display_title; API title stays unchanged", "commit": "b1125d8839482cb7bbae603ddc6d0081bf87532e", "lock_sha256": "4a46cbffbb76f1fcfdb77e50d2106d183fda30a6b178da5f2e2dd5079801dda9", "original_model_blob": "181acf2bf16b4285becb5a5626cf3aa56210211e", "patched_model_sha256": "7f9f207c3cb6c71edfbb25e43b8006e96acf994e09a044e39a519280f6ea7ae7", "repository": "fastapi/full-stack-fastapi-template"}`

## Scope and limitations

- Synthetic project item records only; no production data or traffic.
- Two independent instances of the pinned upstream FastAPI backend with real login and item CRUD routes; synthetic data.
- Sequential interleavings; no concurrent transactions or load test.
- No lock-duration, large backfill, replication, or production deployment verification.
- Rollback means returning to v1 code on the migrated schema, not undoing SQL.
- GO applies only to this fixture and these declared probes.

## Declared application checks observed an incompatibility.

These observations are limited to this workload and do not override the recorded verdict or cleanup state.

- Inspect the first failed operation and its SQLSTATE or value assertion.
- Review old/new field mappings and preserve required old-version behavior through the overlap window.

Cleanup evidence: `{"applications_stopped": true, "connection_closed": true, "schema": "acceptance_eeb61ee97c4d443983af2702ca0f7bda", "schema_state": "removed"}`
