# Compatibility evidence repair plan — 2026-10-24

## Problems and priorities

P0: preserve known numeric overflow. SQLSTATE 22003 from a mapped application
request is a compatibility failure. Baseline, migration, startup, cleanup and
unknown errors must remain INCONCLUSIVE. No broad catch-all HTTP reclassification.

P0: avoid inventing a rollback failure for an uncreated record. Track whether the
new-version create actually acknowledged a commit, independently of its following
read. If it did not, record rollback_new_data as SKIP with a bounded reason and
dependency. Never mark it PASS, remove its row or issue the meaningless read.
If create committed but its paired read failed, still execute rollback_new_data.

The verdict accepts only that specific dependency skip, with a failed new_write
and explicit false write acknowledgement. A skip can never produce GO. Unknown
parent errors, unrelated unknown checks, malformed skips, incomplete lifecycle or
cleanup uncertainty remain INCONCLUSIVE. Known compatibility failures with a valid
dependency skip produce BLOCK. This changes diagnostic completeness honestly,
not the acceptance threshold for a successful run.

P1: make partial execution and coverage understandable. JSON, Markdown and HTML
must preserve the SKIP and its cause. Counts distinguish passing, failed and skipped
checks; phase status must not call a skipped phase fully passed. Coverage text
states that unmapped fields, derived values and other business invariants are
not tested. Do not introduce automatic invariant discovery or claim this warning
solves the underlying coverage gap.

## Acceptance before implementation

- Existing 33 frozen cases retain their original SQL, data and expected verdicts.
  Reruns go into fresh directories and are labeled regression evidence.
- The five previously mismatching cases return BLOCK, retaining actual failed
  operations. New-create failures have 16 evidence rows including one explicit
  dependent SKIP, never a fabricated passing rollback read.
- Real HTTP regression verifies an acknowledged create followed by a failed
  paired read still gets a real rollback read. An unknown create failure with a
  dependency skip, unrelated unknown faults and cleanup failures never become GO
  or a proven compatibility BLOCK.
- Gate tests reject forged, orphaned, unrelated and acknowledged-write skips.
  Report round-trip keeps JSON unchanged; HTML/Markdown explain the skip and scope.
- Freeze six new external SQL cases before changing runtime code. Open them once
  after regression fixes are locked; do not tune to their results. Unconfirmed
  references stay unresolved instead of passing.
- Run unit tests on Python 3.12/3.14, installed-wheel contract on 3.14, disposable
  HTTP/DB regression and fault checks. Independently verify schema/process cleanup.
- Verify report controls and skipped-row visibility in a browser. No deployment,
  package-index publication, new Duo mention or production operation is required.

## Decision rule and remaining limit

Every confirmed case must match the predeclared verdict and exit for its suite
to pass. Regression success does not erase initial failures or establish adoption.
General application safety and independent business-team integration remain
unproven even if every case passes. Current synthetic string CRUD cannot execute
unmapped business operations. Existing alternatives already supply migration
engines and SQL linting; this repair stays inside observed behavioral evidence.
