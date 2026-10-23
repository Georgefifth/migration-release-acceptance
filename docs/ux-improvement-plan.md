# Report UX improvement plan — 2026-10-24

## Audience and core task

A PostgreSQL engineer opens saved CI evidence to decide what failed during
old/new application overlap, inspect rollback behavior and verify the exact run.
The current product is a CLI and offline report, not an online SQL executor.
GitHub Pages will publish a static product introduction and real synthetic sample
reports. It cannot execute migrations, start app processes or hold a database.

## Research and evidence

| Alternative | Strength to learn from | Verified scope, steps and limits |
| --- | --- | --- |
| [Squawk](https://squawkhq.com/docs/renaming-column/), [Playground](https://play.squawkhq.com/) | Direct SQL input, a single Lint action, rule-specific diagnosis/help links. Cleaner initial effort for a known dangerous operation. Open-source CLI. | Actually replaced the public editor content with our Item rename and clicked Lint: four findings including renaming-column. Prior isolated CLI benchmark agrees. No DB needed. Tool interactions were responsive, but no human timing study or cross-product latency benchmark was performed. |
| [Atlas](https://atlasgo.io/testing/migrate), [pricing](https://www.atlasgo.io/pricing), [source](https://github.com/ariga/atlas) | Mature migration workflow, compact SQL assertions and explicit test cleanup. Integrations cover more project ecosystems than ours. | Docs/repository reviewed, no paid account or live Atlas test. Testing requires Pro login (docs mention free and paid Pro); Team starts at USD 9/developer/month plus usage. Applicable free allowance not tested. |
| [pgroll](https://github.com/xataio/pgroll), [user feedback](https://github.com/xataio/pgroll/issues/1032) | Purpose-built simultaneous schema versions, backfills and migration rollback. | Public docs and firsthand multi-role/grant issue reviewed, no production execution. It changes the migration workflow; our tool checks behavior rather than replacing that engine. The reported issue is not evidence our single-role fixture solves it. |
| [Playwright HTML report](https://playwright.dev/docs/test-reporters#html-reporter), [source](https://github.com/microsoft/playwright), [filter feedback](https://github.com/microsoft/playwright/issues/36756) | Outcome filters, details and traces make failure investigation systematic. Its maintained free/open-source reporter is stronger in general test exploration. | Docs and screenshots/user issue reviewed. The issue specifically challenges what All includes and a lost query; closed status does not establish a universal current bug. Keep our filter labels/counts literal and never hide non-executed evidence by implication. |
| [GitLab unit test reports](https://docs.gitlab.com/ci/testing/unit_test_reports/), [source](https://gitlab.com/gitlab-org/gitlab) | Results surfaced directly in MR/pipeline; users need not search logs. JUnit report ingestion works across Free/Premium/Ultimate. | Docs and this project's actual MR/job evidence reviewed. Report ingestion does not fail jobs by itself; exit status remains necessary. Hosting/account quotas vary; no paid plan is proposed. |

Evidence labels: public documentation and actual Squawk use are verified facts.
A better first-investigation flow for our report is an engineering hypothesis
until tested in the browser; user adoption/setup savings remain unverified.
Do not compare app-run durations with a SQL lint pass as equivalent workloads.

## Baseline observations

Developer-run browser observations are saved in reports/ux-review/baseline.json.
At 1280x720 the failure filter starts at y=847.8, below the first viewport, and
all sixteen checks initially display. The label's target height is 16px.
At 390x844 the filter starts at y=1032; the table is about 474px wide inside a
narrower scroll region. Global horizontal overflow is contained, but operation
and result context require horizontal scanning. These are measured UI facts,
not human completion time or success-rate estimates.

## Priorities and acceptance

| Priority | Change | Why worth doing | Acceptance |
| --- | --- | --- | --- |
| P0 | Keep verdict/identity/cleanup semantics and escaped offline output | A pretty report must never imply an approval or falsify saved evidence | Existing report/gate tests pass; JSON values unchanged; mismatched comparison still guarded; no JS/network dependencies in generated reports |
| P1 | Default failed reports to Failures; preserve All checks | Remove scroll-plus-click before the first failure; keep passing setup available | On initial blocked report only 8 failed rows show; one All action restores all 16; passing report starts with all rows; zero-result state explains scope |
| P1 | Native stage-result filters | Inspect rollback/setup without searching sixteen rows | Each phase shows its passing and failing rows in one action, including from Failures; All restores 16; controls work offline and by keyboard |
| P1 | Compact 3-column operation table with stage/app metadata | Keep action/result/SQLSTATE together on mobile | At 390px, readable operation/result evidence with no body overflow; touch labels/links >=44px; visible keyboard focus |
| P2 | Public static entry, report downloads and setup guidance | Judges/users can inspect real behavior without a wheel install or artifact hunt | Homepage identifies sample/source; working sample links/JSON/Markdown; explicit Pages execution limitation; no fake Run/Test/Upload controls |
| P2 | Fresh screenshots and walkthrough of deployed UI | Verify real publication, not a localhost-only result | Open public Pages URL, test all local controls/links and mobile layout, capture screenshots, record current interface with bounded claims |

No paid services, hosted control plane, new AI behaviors or migration engine are
needed. Keep GitLab CI canonical for execution; GitHub is a source/static mirror.

## Design plan and critique before implementation

Color: Paper #fbfcfe; Ink #193647; Waterline #246b78; Issue #a03446;
Pass #246148; Mist #e9f0f5. Use color alongside verdict/status text.
Type: DejaVu Sans with Verdana/sans-serif fallback for a broad, readable technical
review surface; monospace only for actual commit/SQLSTATE/probe identifiers.
Layout: left-aligned evidence sheet with an execution-route spine as the sole
strong visual element, not a generic metrics card grid. Short verdict statement,
compact source/action header, selectable sequential stages, failure-first evidence,
then native source/cleanup disclosures and scope.

    identity / downloads
    verdict + concrete finding          scope summary
    baseline - migration - new - old - mixed - rollback
    next investigation / first failure
    Failures | All checks
    operation + app/stage        result       SQLSTATE
    source / cleanup disclosure
    scope limits

Critique: the existing six boxes risk looking like generic dashboard cards.
Replace their card treatment with selectable positions on one actual execution route.
Retain quiet white space and a single family rather than adding decorative font
pairing, gradients, promotional counts or motion. The sequence numbers are valid
because these are actual ordered phases. Native links/radios/details preserve
keyboard behavior and offline use. Review desktop/mobile screenshots after build.

## Measurement boundary

Compare explicit steps (failure inspection: scroll+filter to zero initial actions;
rollback: manual search to one phase selection) and automated task success. Record local
DOM/layout/control outcomes and deployed HTTP checks. Do not claim user time saved,
market superiority, production safety or a significant latency improvement without
an equivalent controlled study.

Implementation refinement: stage shortcuts are native radio filters, not fragment
links to rows that may be hidden by Failures. This avoids broken navigation or a
JavaScript dependency; selecting a phase includes all its actual recorded checks.
