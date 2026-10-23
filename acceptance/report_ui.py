"""Offline evidence views. Styling and navigation never change a recorded verdict."""
import html
import json
from pathlib import Path
from urllib.parse import quote, urlsplit


STYLE = '''
:root{--paper:#fff;--field:#f3f6fb;--ink:#253957;--link:#2e58c4;--fail:#a23743;--pass:#286451}
*{box-sizing:border-box}body{margin:0;background:var(--field);color:var(--ink);font:16px/1.55 Aptos,"Segoe UI",Arial,sans-serif}
main{max-width:1180px;margin:32px auto;background:var(--paper);padding:36px 44px 28px;border-top:5px solid var(--ink)}
a{color:var(--link);text-underline-offset:3px}a:hover{text-decoration-thickness:2px}a:focus-visible,summary:focus-visible,input:focus-visible+label{outline:3px solid var(--link);outline-offset:4px}
header{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;border-bottom:1px solid #dce3ee;padding-bottom:22px}header p{margin:0}nav{display:flex;flex-wrap:wrap;gap:18px;font-size:14px}
h1{font-size:clamp(26px,3.5vw,38px);line-height:1.2;letter-spacing:-.025em;font-weight:650;max-width:820px;margin:18px 0 14px}
h2{font-size:21px;line-height:1.3;margin:30px 0 14px}h3{font-size:16px;margin:0 0 6px}p{max-width:78ch}small,.muted{font-size:14px;color:#586981}.muted{margin-top:6px}
code,pre{font-family:"SFMono-Regular",Consolas,monospace;font-size:13px;overflow-wrap:anywhere}pre{white-space:pre-wrap;background:var(--field);padding:16px;border-radius:4px}
.verdict{display:inline-block;font-size:14px;font-weight:700;padding:4px 10px;border:1px solid currentColor;border-radius:4px;margin-top:28px}.pass{color:var(--pass)}.fail{color:var(--fail)}.unknown{color:var(--ink)}
.facts{display:flex;flex-wrap:wrap;gap:12px 30px;margin:22px 0 28px}.facts span{font-size:14px}.facts strong{font-size:20px;margin-right:5px;font-weight:650}
.stages{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));margin:24px 0 28px;padding:0;list-style:none;gap:4px}.stages li{background:var(--field);padding:13px 12px;border-bottom:4px solid #a9b6ca;min-height:97px}.stages .pass{border-color:var(--pass)}.stages .fail{border-color:var(--fail)}.stages b{display:block;color:var(--ink);font-weight:600;font-size:15px}.stages small{display:block;margin-top:6px;font-size:12px}
.finding{border-left:4px solid var(--fail);background:#fcf5f6;padding:16px 20px;margin:24px 0}.finding p{margin:3px 0}.finding.neutral{border-color:var(--link);background:var(--field)}
.check-region>input{accent-color:var(--link);margin:0 6px 0 0}.check-region>label{font-size:14px;margin-right:22px;cursor:pointer}.table-shell{overflow-x:auto;margin-top:16px;border:1px solid #dce3ee;border-radius:5px}table{width:100%;border-collapse:collapse;text-align:left;font-size:14px}th{font-weight:600;background:var(--field);padding:12px 14px;border-bottom:1px solid #cbd5e4;white-space:nowrap}td{padding:13px 14px;border-bottom:1px solid #e4e9f1;vertical-align:top}tr:last-child td{border-bottom:0}td p{margin:0}td small{display:block;font-size:12px;margin-top:4px}.check-id{color:#65748b;font-size:11px}td:nth-last-child(2){white-space:nowrap}.result{font-weight:650}.result::before{content:'●';font-size:9px;margin-right:6px}
#fail-only:checked~.table-shell tr[data-result="PASS"]{display:none}#fail-only:checked~.empty-note{display:block}.empty-note{display:none;font-size:14px;margin-top:14px}
details{margin:18px 0;border:1px solid #dce3ee;padding:14px 18px;border-radius:5px}summary{cursor:pointer;font-weight:600}dl{display:grid;grid-template-columns:150px minmax(0,1fr);font-size:14px;gap:8px 20px;margin:18px 0 8px}dt{color:#586981}dd{margin:0;min-width:0}ul.limits{padding-left:20px;font-size:14px;max-width:80ch}ul.limits li{margin:6px 0}footer{border-top:1px solid #dce3ee;margin-top:30px;padding-top:18px;font-size:13px;color:#586981}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:0;margin:26px 0;border:1px solid #dce3ee;border-radius:5px}.pair article{padding:22px}.pair article+article{border-left:1px solid #dce3ee}.pair .verdict{margin-top:6px}.pair h2{margin:0 0 8px}.pair p{margin:10px 0}.comparison td:first-child{min-width:240px}
@media(max-width:760px){main{margin:0;padding:22px 18px;border-top-width:4px}header{display:block}nav{margin-top:14px;gap:14px}.stages{grid-template-columns:repeat(3,minmax(0,1fr))}.stages li{min-height:84px}th,td{padding:10px}dl{grid-template-columns:1fr;gap:3px}dd{margin-bottom:9px}.pair{grid-template-columns:1fr}.pair article+article{border-left:0;border-top:1px solid #dce3ee}.facts{gap:8px 20px}}
@media print{body{background:white}main{margin:0;max-width:none;padding:12px}nav,.check-region>input,.check-region>label{display:none}.table-shell{overflow:visible}tr[data-result]{display:table-row!important}details{break-inside:avoid}a{color:inherit}h2{break-after:avoid}}
'''
STAGES = [('baseline', 'Baseline'), ('migration', 'Migration'), ('target', 'New app'),
          ('rollout', 'Old app'), ('mixed', 'Mixed versions'), ('app_rollback', 'App rollback')]


def esc(value):
    return html.escape(str(value), quote=True)


def link(url, label):
    try:
        parsed = urlsplit(str(url))
        allowed = parsed.scheme in {'https', 'http'} and parsed.hostname and not parsed.username and not parsed.password
    except ValueError:
        allowed = False
    return f'<a href="{esc(url)}">{esc(label)}</a>' if allowed else esc(label)


def tone(status):
    return {'PASS': 'pass', 'GO_WITHIN_SCOPE': 'pass', 'FAIL': 'fail', 'BLOCK': 'fail'}.get(status, 'unknown')


def shell(title, body):
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{esc(title)}</title><style>{STYLE}</style></head><body><main>{body}'
            '</main></body></html>')


def badge(status):
    return f'<span class="verdict {tone(status)}">{esc(status)}</span>'


def result(status, state=None):
    suffix = ' / ' + esc(state) if state else ''
    return f'<span class="result {tone(status)}">{esc(status)}{suffix}</span>'


def introduction(report):
    checks = report.get('checks', [])
    failures = [c for c in checks if c.get('status') != 'PASS']
    if not report.get('completed') or not report.get('cleanup_ok') or report.get('verdict') == 'INCONCLUSIVE':
        return 'This run cannot establish compatibility.'
    if report.get('verdict') == 'GO_WITHIN_SCOPE' and checks and not failures:
        return 'All declared application checks passed.'
    migration_passed = any(c.get('id') == 'migration' and c.get('status') == 'PASS' for c in checks)
    old_failed = any(c.get('id') in {'old_read', 'old_write', 'rollback_read', 'rollback_new_data'} for c in failures)
    if migration_passed and old_failed:
        return 'The migration passed. Old-version requests failed.'
    return 'Application compatibility checks failed.' if failures else 'Review the recorded acceptance evidence.'


def html_report(report):
    checks = report.get('checks', [])
    failed = [c for c in checks if c.get('status') != 'PASS']
    passed = len(checks) - len(failed)
    scenario = report['scenario']
    navigation = (f'<a href="{quote(str(scenario), safe="")}.json">JSON evidence</a>'
                  f'<a href="{quote(str(scenario), safe="")}.md">Markdown</a>'
                  + ('<a href="comparison.html">Compare candidates</a>' if scenario in {'breaking', 'expand'} else ''))
    body = '<header><div><p><strong>Migration acceptance</strong></p><p class="muted">' + esc(report.get('workload', 'customer-reference')) + '<br>Commit <code title="' + esc(report['commit']) + '">' + esc(report['commit'][:12]) + '</code></p></div><nav aria-label="Report files">' + navigation + '</nav></header>'
    body += badge(report['verdict']) + '<h1>' + esc(introduction(report)) + '</h1>'
    body += '<p class="muted">Recorded evidence for the ' + esc(scenario) + ' candidate. The result applies to the declared probes and fixture.</p>'
    body += f'<div class="facts"><span><strong>{passed}/{len(checks)}</strong> checks passed</span><span><strong>{len(failed)}</strong> failed</span><span>Execution: <strong>{"complete" if report.get("completed") else "incomplete"}</strong></span><span>Cleanup: <strong>{"complete" if report.get("cleanup_ok") else "unconfirmed"}</strong></span></div>'
    body += '<ol class="stages" aria-label="Acceptance sequence">'
    for stage, label in STAGES:
        group = [c for c in checks if c.get('stage') == stage]
        bad = sum(c.get('status') != 'PASS' for c in group)
        status = 'FAIL' if bad else 'PASS' if group else 'NOT RUN'
        description = f'{bad} failed / {len(group)} checks' if bad else f'{len(group)} passed' if group else 'No checks recorded'
        body += f'<li class="{tone(status)}"><b>{label}</b><small>{esc(description)}</small></li>'
    body += '</ol>'
    if report.get('verdict') == 'INCONCLUSIVE' or not report.get('completed') or not report.get('cleanup_ok'):
        body += '<aside class="finding neutral"><h3>Resolve the evidence gap first</h3><p>Inspect the execution details, restore successful setup and cleanup, then rerun before judging the migration.</p></aside>'
    elif failed:
        first = failed[0]
        body += '<aside class="finding"><h3>First recorded failure</h3><p><strong>' + esc(first['operation']) + '</strong> / ' + esc(first['version']) + '</p>'
        if first.get('sqlstate') == '42703':
            body += '<p>SQLSTATE <code>42703</code>: an application requested a column that is absent from this schema.</p><p>Review the failing operation and preserve the fields needed by old versions during the rollout window.</p>'
        else:
            body += '<p>Inspect the failing operation and its error classification before changing the candidate.</p>'
        body += '</aside>'
    body += '<section class="check-region" aria-labelledby="checks-heading"><h2 id="checks-heading">Operation evidence</h2>'
    body += f'<input type="radio" name="check-filter" id="all-checks" checked><label for="all-checks">All checks ({len(checks)})</label><input type="radio" name="check-filter" id="fail-only"><label for="fail-only">Failures ({len(failed)})</label>'
    if not failed:
        body += '<p class="empty-note">No failed checks were recorded. Check execution and cleanup status before interpreting this result.</p>'
    body += '<div class="table-shell"><table><thead><tr><th scope="col">Stage</th><th scope="col">Application</th><th scope="col">Operation</th><th scope="col">Result</th><th scope="col">SQLSTATE</th></tr></thead><tbody>'
    labels = dict(STAGES)
    for c in checks:
        status = c.get('status', 'UNKNOWN')
        body += f'<tr data-result="{esc(status)}"><td>{esc(labels.get(c["stage"], c["stage"]))}</td><td>{esc(c["version"])}</td><td><p>{esc(c["operation"])}</p><small class="check-id">{esc(c["id"])}</small>'
        if c.get('failure_kind'):
            body += '<small>Classification: ' + esc(c['failure_kind']) + '</small>'
        body += '</td><td>' + result(status) + '</td><td><code>' + esc(c.get('sqlstate') or '—') + '</code></td></tr>'
    body += '</tbody></table></div></section>'
    body += '<details><summary>Run identity and source</summary><dl>'
    for label, value in [('Candidate', scenario), ('Commit', report['commit']), ('Run ID', report['run_id']), ('Created', report.get('created_at', 'unspecified')), ('Transport', report.get('transport', 'unspecified')), ('Fixture SHA-256', report['fixture_sha256'])]:
        body += '<dt>' + esc(label) + '</dt><dd><code>' + esc(value) + '</code></dd>'
    if report.get('pipeline_url'):
        body += '<dt>Pipeline</dt><dd>' + link(report['pipeline_url'], 'Open CI pipeline') + '</dd>'
    body += '</dl>'
    if report.get('provenance'):
        body += '<h3>Upstream provenance</h3><pre>' + esc(json.dumps(report['provenance'], indent=2)) + '</pre>'
    body += '</details>'
    if report.get('error'):
        body += '<details open><summary>Execution details</summary><pre>' + esc(json.dumps(report['error'], indent=2)) + '</pre></details>'
    body += '<h2>What this run covers</h2><ul class="limits">' + ''.join('<li>' + esc(v) + '</li>' for v in report.get('limitations', [])) + '</ul>'
    body += '<footer>A recorded GO_WITHIN_SCOPE is evidence for these probes. Merge and deployment remain human decisions.</footer>'
    return shell('Migration acceptance: ' + report['verdict'], body)


def comparison_gap(left, right):
    if left.get('scenario') != 'breaking' or right.get('scenario') != 'expand':
        return 'The candidate labels do not identify a breaking/expand pair.'
    for report in (left, right):
        if (any(not isinstance(report.get(key), str) or not report[key]
                for key in ('workload', 'application_factory', 'transport'))
                or not isinstance(report.get('provenance'), dict)):
            return 'Workload, adapter, transport or provenance identity is missing.'
    if left.get('commit') in {None, '', 'local-development'} or left.get('commit') != right.get('commit'):
        return 'The runs do not identify the same verified source commit.'
    for key in ('workload', 'application_factory', 'provenance', 'transport', 'postgres_version'):
        if left.get(key) != right.get(key):
            return 'The workload, adapter or upstream provenance differs between these runs.'
    for report in (left, right):
        if not report.get('completed') or not report.get('cleanup_ok'):
            return 'Execution or cleanup is incomplete in at least one run.'
    a = [c.get('id') for c in left.get('checks', [])]
    b = [c.get('id') for c in right.get('checks', [])]
    if not a or len(a) != len(set(a)) or len(b) != len(set(b)) or set(a) != set(b):
        return 'The runs do not contain the same complete, unique probe set.'
    right_by_id = {c['id']: c for c in right['checks']}
    for c in left['checks']:
        if any(c.get(key) != right_by_id[c['id']].get(key) for key in ('stage', 'version', 'operation')):
            return 'The probe definitions differ between these runs.'
    return None


def comparison_report(left=None, right=None):
    navigation = ''.join('<a href="' + name + '.html">' + label + '</a>'
                         for name, label, report in [('breaking', 'Breaking run', left), ('expand', 'Expand run', right)]
                         if report is not None)
    body = '<header><p><strong>Migration acceptance</strong></p><nav aria-label="Run reports">' + navigation + '</nav></header><h1>Compare candidate behavior.</h1>'
    if left is None or right is None:
        body += '<aside class="finding neutral"><h3>A second run is needed</h3><p>Run both breaking and expand candidates into this report directory to compare their operation evidence.</p></aside>'
        return shell('Candidate comparison', body)
    gap = comparison_gap(left, right)
    if gap:
        body += '<aside class="finding neutral"><h3>These runs cannot establish a direct comparison</h3><p>' + esc(gap) + '</p><p>Rerun both candidates from the same source and workload, with complete execution and cleanup.</p></aside>'
    else:
        body += '<p>These independent runs share a source commit, workload, adapter, upstream provenance and probe set. Their different SQL fixtures are the candidates being compared.</p>'
    body += '<div class="pair">'
    for name, report in [('Breaking', left), ('Expand', right)]:
        passed = sum(c.get('status') == 'PASS' for c in report.get('checks', []))
        body += f'<article><h2>{name} candidate</h2>{badge(report["verdict"])}<p>{passed}/{len(report.get("checks", []))} checks passed</p><p>Commit <code>{esc(report["commit"])}</code></p><a href="{name.lower()}.html">Open full run</a></article>'
    body += '</div>'
    if not gap:
        right_checks = {c['id']: c for c in right['checks']}
        body += '<h2>The same operations, two candidates</h2><div class="table-shell"><table class="comparison"><thead><tr><th scope="col">Operation</th><th scope="col">Breaking</th><th scope="col">Expand</th></tr></thead><tbody>'
        for c in left['checks']:
            other = right_checks[c['id']]
            body += '<tr><td>' + esc(c['operation']) + '<small>' + esc(c['version']) + '</small></td><td>' + result(c['status'], c.get('sqlstate')) + '</td><td>' + result(other['status'], other.get('sqlstate')) + '</td></tr>'
        body += '</tbody></table></div>'
    body += '<h2>Run identities</h2><p>Breaking: <code>' + esc(left['run_id']) + '</code><br>Expand: <code>' + esc(right['run_id']) + '</code></p>'
    body += '<footer>Each verdict retains its original scope. Comparison does not establish production safety or approve deployment.</footer>'
    return shell('Candidate comparison', body)


def write_comparison(output):
    reports = []
    for name in ('breaking', 'expand'):
        try:
            candidate = json.loads((output / (name + '.json')).read_text())
            valid = (isinstance(candidate, dict) and candidate.get('scenario') == name
                     and all(isinstance(candidate.get(k), str) for k in ('commit', 'run_id', 'verdict'))
                     and isinstance(candidate.get('checks'), list)
                     and all(isinstance(c, dict) and all(isinstance(c.get(k), str)
                         for k in ('id', 'stage', 'version', 'operation', 'status')) for c in candidate['checks']))
            reports.append(candidate if valid else None)
        except (OSError, ValueError):
            reports.append(None)
    (output / 'comparison.html').write_text(comparison_report(*reports))
