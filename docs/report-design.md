# Report experience

Audience: the PostgreSQL engineer reviewing old/new application overlap. Locate
failed behavior, inspect a specific execution phase and verify source/cleanup.
The report is evidence, never an automatic deployment approval.

Palette: Paper #fbfcfe, Mist #e9f0f5, Ink #193647, Waterline #246b78,
Issue #a03446, Pass #246148. DejaVu Sans/Verdana for readable evidence;
monospace only for actual commit/probe/SQLSTATE identifiers. No external assets.

The ordered execution route is the single strong visual device. Its six native
radio labels filter phase evidence, including passing rows even when the run
opens in Failures. All checks restores every recorded row. Numbers correspond
to actual ordered phases, not decorative markers. Filter labels/counts remain
literal; incomplete phases say Not run and expose an explicit empty state.

    identity / evidence downloads
    verdict + specific finding / completion and cleanup facts
    baseline - migration - new - old - mixed - rollback
    bounded investigation guidance
    All checks | Failures
    operation + stage/version       result        SQLSTATE
    source and cleanup disclosures
    declared scope

Failed runs default to Failures; passing/zero-check runs default to All checks.
This removes a filter-selection step, not all scrolling. A phase selection is
one action; reading rows may still require scrolling. The three-column evidence
table retains stage/version as operation metadata so mobile review does not
require a horizontal pan. Preserve native keyboard radio behavior, 44px primary
control targets, source/details disclosure, print visibility and a skip link.

HTML contains no JavaScript, external fonts or network assets. Evidence remains
escaped and saved JSON/verdicts are unchanged by view filters. Compare only
matching complete source/workload/adapter/provenance/probe evidence. No dashboard,
risk percentage, motion or automatic repair is introduced.

See [research, baseline and acceptance plan](ux-improvement-plan.md). Developer
browser measurements and task checks are not human usability or adoption evidence.
