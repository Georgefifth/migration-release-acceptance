# Report experience

Audience: the engineer reviewing a PostgreSQL migration. The primary job is to
locate broken application behavior, then inspect evidence and compare candidates.

Palette: white #ffffff, field #f3f6fb, ink #253957, link #2e58c4,
failure #a23743, success #286451. Use Aptos/Segoe UI/Arial for readable interface
text and a monospace only for source identifiers. Keep all assets offline.

Layout, left aligned:

    Run identity                         JSON / Markdown
    Recorded verdict + plain-language finding
    Baseline — Migration — New app — Old app — Mixed — Rollback
    First failure / next investigation
    All checks | Failures     operation evidence table
    Source, run identity and limitations

The stage strip is an actual sequence of executed checks, not decorative steps.
It is the one strong visual feature; surrounding content stays quiet. Status is
always expressed in words as well as color. Avoid a dashboard card grid, large
score, invented risk percentage, or automatic production approval.

Review: a generic developer dashboard would emphasize build counts and charts.
This report instead leads with the specific migration/application contrast and
keeps the operation, app version and SQLSTATE together. A two-run comparison
requires matching commit, workload, adapter, provenance and complete probe sets.
Never present different or incomplete evidence as a verified before/after pair.

Use native disclosure and radio controls. Reports work without JavaScript,
external fonts or a server; all evidence is HTML-escaped. Links allow only HTTP(S)
for supplied pipeline URLs. Mobile tables scroll inside the report, not the page.
