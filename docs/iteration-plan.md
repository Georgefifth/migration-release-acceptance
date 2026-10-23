# Iteration plan

The intended product is a usable compatibility acceptance tool, not a growing
collection of examples. Keep the following release boundaries explicit.

## Completed technical milestone: installation and downstream invocation

Ship a wheel and installed commands that run from an application's own project.
Require an isolated package-contract CI job with packaged SQL, preflight, actual
HTTP/DB execution, correct release exits and offline rendering. A source-tree-only
test is insufficient. Do not publish on PyPI as part of this iteration.

## Current iteration: actionable failure evidence

Record the actual failed step and distinguish application stop, schema removal
and connection close. Explain what to check next without inventing a root cause
or changing verdicts. Validate with controlled database/startup/SQL/cleanup faults,
including passing CRUD with failed cleanup. Preserve conservative behavior for
missing evidence and keep private exception content out of artifacts.

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
