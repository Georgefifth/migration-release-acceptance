# External expansion 4 — pre-fix plan

The frozen 24-case corpus extends evaluation to enums, identity, rules, triggers
and RLS under a NOSUPERUSER NOBYPASSRLS role. Sixteen development cases ran before
fixes: ten matched and six known incompatibilities became INCONCLUSIVE. Eight
holdout cases remain unopened. Every reference probe confirmed its frozen result.
No expected label, SQL statement or input will change after these results.

## Repair scope and acceptance

1. Recognize mapped-request 22P02 (invalid text representation), 428C9 (generated
   always identity rejection) and 42501 (insufficient privilege) as compatibility
   failures after successful baseline/migration. Lifecycle failures remain
   INCONCLUSIVE. Do not generalize arbitrary HTTP/auth errors into BLOCK.
2. Give the reviewed synthetic HTTP protocol a bounded record_missing error for a
   genuinely absent expected record. Only HTTP 404 plus that exact protocol code
   maps automatically. Unknown-route 404, generic 500, malformed response and
   arbitrary exception text remain unknown. An explicitly reviewed custom adapter
   may use the same semantic reason for a confirmed absent record.
3. Validate SQLSTATE in ApplicationError itself as five ASCII uppercase letters/
   digits, including direct custom-adapter calls. Keep exception text empty; do
   not leak rows, DSNs or unknown supplied reason text.
4. Observe booleans for the runner connection's superuser/BYPASSRLS capability.
   Do not serialize the role name or claim the app uses that role. Add a precise
   report limitation for privileged runner connections. Role owners can bypass
   RLS without FORCE even when both booleans are false; never claim an RLS audit.

Regression acceptance: all sixteen development labels/exits must match with the
same low-privilege conditions; retain original failures. Validate known missing
records through actual HTTP, rather than only mocking exception classes. Existing
SKIP acknowledgement, unknown errors, cleanup guards and previous 39 contexts must
remain correct. Unit checks cover protocol spoofing/wrong status, invalid Unicode
SQLSTATE, direct exception privacy and unknown-route separation. Fresh installed
wheel and pinned FastAPI cases must retain their expected behavior.

Lock fixes before the eight new holdout cases. Open once, report all results and
leave any failure unresolved or failed; no tuning to that set. UI/report changes
must preserve stored verdicts and indicate runner-only role evidence. This stays
a synthetic adapter evaluation and does not count as another real-team integration.
