"""Publish reviewed synthetic report samples as a static site; never execute SQL."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from acceptance.report import load_report, write_reports
from acceptance.report_ui import STYLE, esc


def build(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / 'docs/demo-evidence.json').read_text())
    declared = {r['scenario']: r for r in manifest['upstream']['runs']}
    declared.update({r['candidate']: r for r in manifest['release_gates']})
    reports = []
    for name in ('breaking', 'expand', 'item-title-storage', 'rename-title'):
        report = load_report(ROOT / 'demo/evidence' / (name + '.json'))
        expected = declared[name]
        if (report['commit'] != manifest['evidence_commit'] or report['run_id'] != expected['run_id']
                or report['verdict'] != expected['verdict'] or len(report['checks']) != 16
                or not report['completed'] or not report['cleanup_ok']):
            raise ValueError('Static sample identity or scope does not match the reviewed manifest')
        reports.append(report)
    destination = output / 'reports'
    for report in reports:
        write_reports(report, destination)
    for page in destination.glob('*.html'):
        text = page.read_text()
        text = text.replace('<nav aria-label="Report files">', '<nav aria-label="Report files"><a href="../index.html">Overview</a>')
        text = text.replace('<nav aria-label="Run reports">', '<nav aria-label="Run reports"><a href="../index.html">Overview</a>')
        page.write_text(text)
    style = STYLE + '''
.site-intro{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:36px;padding:20px 0 28px;border-bottom:1px solid var(--line)}
.site-intro h1{font-size:clamp(30px,4vw,48px);max-width:20ch;margin-top:12px}.site-intro p{font-size:15px;max-width:58ch}.actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}.action{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:10px 17px;border:1px solid var(--link);border-radius:6px;text-decoration:none;font-size:14px;font-weight:600}.action.primary{background:var(--link);color:white}.sample-summary{align-self:center;padding:20px 22px;border:1px solid var(--line);border-radius:9px;background:var(--field)}.sample-summary h2{font-size:17px;margin:0 0 16px}.sample-summary dl{grid-template-columns:1fr auto;margin:0;font-size:13px;gap:12px}.sample-summary dd{font-weight:700}.sample-summary p{font-size:12px;margin-bottom:0}.site-section{margin:28px 0}.site-section h2{max-width:35ch}.two-column{display:grid;grid-template-columns:1fr 1fr;gap:32px}.two-column p,.two-column li{font-size:14px}.setup-list{padding-left:22px}.setup-list li{padding-left:5px;margin:14px 0}.setup-list p{margin:5px 0;font-size:13px}.setup-list strong{font-size:14px}.evidence-links{display:flex;flex-wrap:wrap;gap:10px 22px}.evidence-links a{display:inline-flex;align-items:center;min-height:44px;font-size:13px}.site-notice{font-size:13px;margin:22px 0;padding:14px 18px;background:var(--field);border-radius:6px}.site-intro .muted{font-size:12px}a.action:focus-visible{outline-offset:4px}
@media(max-width:760px){.site-intro,.two-column{grid-template-columns:1fr;gap:18px}.site-intro{padding-top:12px}.site-intro h1{font-size:34px}.sample-summary{padding:18px}.sample-summary dl{grid-template-columns:1fr auto}.sample-summary dd{margin:0}.actions .action{width:100%}.site-section{margin:24px 0}}
'''
    gitlab = 'https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43208246/showcase'
    github = 'https://github.com/Georgefifth/migration-release-acceptance'
    page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Inspect old/new PostgreSQL application compatibility through real HTTP evidence, mixed writes and application rollback."><title>Migration acceptance — inspect a release before old code breaks</title><style>''' + style + '''</style></head><body><a class="skip-link" href="#main-content">Skip to content</a><main id="main-content">
<header><div><p><strong>Migration acceptance</strong></p><p class="muted">PostgreSQL application compatibility</p></div><nav aria-label="Main navigation"><a href="reports/comparison.html">Compare samples</a><a href="#run-locally">Use in your CI</a><a href="''' + github + '''">Source code</a></nav></header>
<section class="site-intro"><div><h1>Will old code still work after this migration?</h1><p>A successful migration and passing new-version tests can miss broken old requests. Rehearse old/new reads, mixed writes and a return to old code before a human decides to release.</p><div class="actions"><a class="action primary" href="reports/breaking.html">Inspect blocked run</a><a class="action" href="reports/comparison.html">Compare candidates</a></div><p class="muted">Real saved CI results from a pinned public FastAPI backend. Synthetic data only.</p></div>
<aside class="sample-summary"><h2>The same application, two candidates</h2><dl><dt>Rename the old column</dt><dd class="fail">8 failed</dd><dt>Keep both representations</dt><dd class="pass">16 passed</dd><dt>Execution and cleanup</dt><dd>Complete</dd></dl><p>The reports name the exact source commit, run and SQLSTATE. They are saved evidence, not a live test.</p></aside></section>
<aside class="site-notice"><strong>This site is a static report viewer.</strong> It cannot run SQL, start applications or connect to a database. Run acceptance with the CLI and a disposable PostgreSQL service, locally or in GitLab CI.</aside>
<section class="site-section two-column"><div><h2>Inspect the failure, then the evidence</h2><p>Blocked reports open on failed checks. Select a phase to inspect its complete evidence, including successful setup and restart. All checks restores the whole run.</p><p>In this sample, migration and new-version requests pass. Old, mixed-version and rollback requests fail with SQLSTATE 42703. Restarting old code does not restore the old database schema.</p><a class="action" href="reports/expand.html">Inspect compatible run</a></div><div><h2>Keep the scope visible</h2><p>GO_WITHIN_SCOPE applies only to the declared synthetic workflow. Sequential tests do not establish concurrent behavior, lock duration, large-backfill performance or production safety.</p><p>A human controls merge and deployment. The example synchronization SQL is fixture-specific, not a universal migration recipe.</p></div></section>
<section class="site-section" id="run-locally"><h2>Use your application's own checks</h2><ol class="setup-list"><li><strong>Install the reviewed wheel in your test environment.</strong><p>The package is not on PyPI. Use the build artifact and <a href="''' + gitlab + '''/-/blob/codex/migration-acceptance-mvp/docs/installation.md">installation guide</a>.</p></li><li><strong>Map a synthetic business operation.</strong><p>Provide reviewed startup, authentication, HTTP/ID mapping, baseline data and candidate SQL. <a href="''' + gitlab + '''/-/blob/codex/migration-acceptance-mvp/docs/application-integration.md">Read the adapter contract</a>.</p></li><li><strong>Preflight, then run on a disposable database.</strong><p>Preflight imports trusted configuration, but does not start an app or access a database. Execution requires your disposable DB settings.</p><pre>migration-accept --integration project_acceptance:integration --candidate title-storage --check
migration-accept --integration project_acceptance:integration --candidate title-storage --output reports/title-storage</pre></li></ol><p class="source-note">Application integration still needs reviewed code. Independent setup savings and customer adoption are unverified.</p></section>
<section class="site-section"><h2>Follow the actual release evidence</h2><p class="source-note">Sample source: <code>''' + esc(manifest['evidence_commit']) + '''</code>. The comparison uses known-outcome regression runs. The named release jobs below independently preserve release exit codes.</p><div class="evidence-links"><a href="reports/rename-title.html">Blocked release report</a><a href="reports/item-title-storage.html">Compatible release report</a><a href="''' + gitlab + '''/-/pipelines/2980661072">Failed release pipeline</a><a href="''' + gitlab + '''/-/pipelines/2980660966">Passing release pipeline</a><a href="''' + gitlab + '''/-/merge_requests/1#note_4075490215">Verified Duo explanation</a><a href="build.json">Site build identity</a></div><p class="source-note">The Duo note reviews commit 01126ed8, a later documentation/tooling head. It is not a review of the comparison's older run IDs.</p></section>
<footer>Open-source MIT prototype. Saved evidence, explicit scope, human release decisions. No automatic repair, merge or deployment.</footer></main></body></html>'''
    (output / 'index.html').write_text(page)
    (output / '.nojekyll').write_text('')
    renderer = ROOT / 'acceptance/report_ui.py'
    identity = dict(renderer_version='0.1.6', renderer_sha256=hashlib.sha256(renderer.read_bytes()).hexdigest(),
                    sample_evidence_commit=manifest['evidence_commit'], static_only=True,
                    samples=[dict(candidate=r['scenario'], run_id=r['run_id'], verdict=r['verdict']) for r in reports],
                    files={str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted(output.rglob('*')) if p.is_file() and p.name != 'build.json'})
    (output / 'build.json').write_text(json.dumps(identity, indent=2) + '\n')
    print('Built static report site: ' + str(output.resolve()))
    return identity


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'site')
    build(parser.parse_args().output)
