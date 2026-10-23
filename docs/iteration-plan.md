# Iteration plan

The intended product is a usable compatibility acceptance tool, not a growing
collection of examples. Keep the following release boundaries explicit.

## Completed technical milestone: installation and downstream invocation

Ship a wheel and installed commands that run from an application's own project.
Require an isolated package-contract CI job with packaged SQL, preflight, actual
HTTP/DB execution, correct release exits and offline rendering. A source-tree-only
test is insufficient. Do not publish on PyPI as part of this iteration.

## Completed technical milestone: actionable failure evidence

Record the actual failed step and distinguish application stop, schema removal
and connection close. Explain what to check next without inventing a root cause
or changing verdicts. Validate with controlled database/startup/SQL/cleanup faults,
including passing CRUD with failed cleanup. Preserve conservative behavior for
missing evidence and keep private exception content out of artifacts.

## Completed technical milestone: use application evidence in the actual release job

The real FastAPI integration must feed release-acceptance directly, not only a
green expected-outcome self-test. Verify both selected candidates at the same
source commit: the compatible candidate passes and the deliberately breaking
candidate fails the job/pipeline with BLOCK. Preserve reports on failure and
document the command for a project's existing CI without adding deployment.

## Current iteration: catch integration mistakes before resource startup

Preflight binds inspectable factory/initializer/class-method signatures without
invoking them, reports missing class protocol methods and rejects unsupported
async operations. A candidate typo fails even in check mode. Verify the installed
wheel rejects invalid configuration without a database and still preserves real
GO/BLOCK/INCONCLUSIVE runs from a separate generated project. Dynamic factories
and descriptor behavior remain runtime checks. This is an early-error improvement,
not evidence of measured onboarding savings.

## Next: independently reproducible project setup

Have someone follow installation and adapter instructions without coaching when a
participant becomes available. Record required edits, help events and the existing
CI alternative. Until then, generated downstream and public FastAPI integrations
are technical evidence only. They cannot establish setup savings or market value.

## Then: narrow improvements justified by failures

Fix observed import/startup/auth/fixture/report problems that block completion.
Preserve INCONCLUSIVE for missing evidence. Do not add more generic infrastructure,
a hosted UI, automatic migration repair or broader workflows in place of useful
application-specific checks and clear results.

## Delivery boundary

Keep source, built artifact, actual run IDs and demo snapshot distinguishable.
Verify the final CI head before submission. Record and play back the actual demo
video before calling it complete. A script, offline report bundle and green
synthetic tests alone do not establish a finished, independently validated product.
