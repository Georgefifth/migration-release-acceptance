# Static deployment and source mirrors

GitLab remains the canonical execution and Duo project:
https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase

The GitHub source/static mirror is:
https://github.com/Georgefifth/migration-release-acceptance

The intended Pages URL is:
https://georgefifth.github.io/migration-release-acceptance/

Publication is not verified merely because these URLs are written here. The
actual deployment check and build identity must be inspected before reporting it
as live. GitHub Pages hosts only HTML/JSON/Markdown and static assets: it cannot
run the Python acceptance CLI, application processes, SQL or PostgreSQL. There
is no upload form, fake execution button, hosted database or server-side secret.

## Build and verify

```sh
python3 -m unittest discover -s tests -v
python3 tools/build_site.py --output site
```

The builder uses only four explicitly reviewed synthetic CI reports in
demo/evidence/. It verifies their run IDs, source SHA, completion and verdict
against docs/demo-evidence.json before writing report pages. The resulting
build.json identifies renderer version/hash, sample source/run IDs and every
static file hash. Rendering an old sample does not make it evidence for new code.

Deploy only the generated static output to the gh-pages branch root, with
.nojekyll. Enable Pages from that branch. Keep source on main and retain GitLab
as the execution remote; do not upload .env, reports/, .git, virtual environments,
upstream clones or raw job traces. A scoped secret-pattern/allowlist check precedes
publication. A pattern scan is not a proof that every possible secret is absent.

Open the real Pages URL and test overview/report/compare navigation, phase and
result filters, disclosures, evidence downloads, keyboard interaction and mobile
layout. Compare its build.json with the local intended build, and save actual
screenshots/recording. Source code publication and a successful local build alone
do not establish a working public deployment.

No merge, production database deployment or package-index publication is implied.
The fixed Duo note reviews 01126ed8; later UI commits need their own CI and cannot
inherit its current-head identity.
