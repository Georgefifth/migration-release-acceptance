"""Offline evidence views. Styling and navigation never change a recorded verdict."""
import html
import json
from pathlib import Path
from urllib.parse import quote, urlsplit
from .diagnostics import troubleshooting


STYLE = '''
:root{--paper:#fbfcfe;--field:#e9f0f5;--ink:#193647;--link:#246b78;--fail:#a03446;--pass:#246148;--line:#cddce5;--muted:#506779}
*{box-sizing:border-box}html{scroll-padding-top:24px}body{margin:0;background:var(--field);color:var(--ink);font:16px/1.6 "DejaVu Sans",Verdana,sans-serif}main{max-width:1200px;margin:28px auto;background:var(--paper);padding:30px 40px 26px;border-radius:12px;border:1px solid var(--line)}
a{color:var(--link);text-underline-offset:4px}a:hover{text-decoration-thickness:2px}a:focus-visible,summary:focus-visible{outline:3px solid var(--link);outline-offset:4px}.skip-link{position:absolute;left:18px;top:-80px;padding:12px;background:white;z-index:5}.skip-link:focus{top:8px}
header{display:flex;align-items:center;justify-content:space-between;gap:20px;border-bottom:1px solid var(--line);padding-bottom:18px}header p{margin:0}header strong{font-size:17px}nav{display:flex;flex-wrap:wrap;gap:6px 12px;font-size:13px}nav a{display:inline-flex;align-items:center;min-height:44px;padding:6px 9px;border:1px solid var(--line);border-radius:5px;text-decoration:none;background:white}nav a:hover{border-color:var(--link);background:var(--field)}
h1{font-size:clamp(25px,3.3vw,38px);line-height:1.23;letter-spacing:-.035em;font-weight:700;max-width:27ch;margin:14px 0 12px}h2{font-size:21px;line-height:1.3;letter-spacing:-.02em;margin:28px 0 14px}h3{font-size:16px;margin:0 0 6px}p{max-width:76ch}small,.muted{font-size:13px;color:var(--muted)}.muted{margin-top:6px}.hero{padding:4px 0 8px}.hero>p{margin:10px 0}
code,pre{font-family:"DejaVu Sans Mono",Consolas,monospace;font-size:12px;overflow-wrap:anywhere}pre{white-space:pre-wrap;background:var(--field);padding:16px;border-radius:6px;max-width:100%}.verdict{display:inline-flex;align-items:center;gap:8px;font-size:13px;font-weight:700;padding:6px 11px;border:1px solid currentColor;border-radius:5px;margin-top:24px}.verdict:before{content:'';width:7px;height:7px;background:currentColor;border-radius:50%}.pass{color:var(--pass)}.fail{color:var(--fail)}.unknown{color:var(--ink)}.facts{display:flex;flex-wrap:wrap;gap:8px 24px;padding:14px 0 18px;border-bottom:1px solid var(--line)}.facts span{font-size:13px}.facts strong{font-weight:700;margin-right:4px}
.check-region{position:relative;border:0;padding:0;margin:0;min-width:0}.filter-input{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}
.stages{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));margin:24px 0 20px;padding:0;list-style:none;gap:0}.stages li{position:relative;min-width:0;border-top:3px solid var(--line);padding-top:8px}.stages label{display:block;position:relative;cursor:pointer;padding:9px 8px 10px;border-radius:6px;min-height:78px}.stages label:hover{background:var(--field)}.stage-number{display:inline-flex;align-items:center;justify-content:center;width:23px;height:23px;background:var(--paper);border:1px solid currentColor;border-radius:50%;font-size:11px;font-weight:700;margin-bottom:7px}.stages b{display:block;color:var(--ink);font-size:13px;line-height:1.4}.stages small{display:block;font-size:11px;margin-top:3px}.stages .pass{border-color:var(--pass)}.stages .fail{border-color:var(--fail)}
.finding{overflow-wrap:anywhere;border-left:4px solid var(--fail);background:#f9eff2;padding:14px 18px;margin:18px 0 22px;border-radius:0 6px 6px 0}.finding p{margin:3px 0;font-size:14px}.finding.neutral{border-color:var(--link);background:var(--field)}.finding ul{padding-left:18px;font-size:14px}
.evidence-toolbar{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin:24px 0 8px}.evidence-toolbar h2{margin:0}.filters{display:flex;gap:4px;border:1px solid var(--line);border-radius:7px;padding:3px;background:var(--field)}.filters label{font-size:13px;cursor:pointer;display:flex;align-items:center;justify-content:center;min-height:44px;padding:8px 14px;border-radius:4px;border:1px solid transparent}.filters label:hover{background:white}.view-note{font-size:13px;color:var(--muted);margin:6px 0 12px;display:none}
#all-checks:checked~.evidence-toolbar label[for="all-checks"],#fail-only:checked~.evidence-toolbar label[for="fail-only"]{background:var(--paper);border-color:var(--line);color:var(--ink);font-weight:700}
#all-checks:focus-visible~.evidence-toolbar label[for="all-checks"],#fail-only:focus-visible~.evidence-toolbar label[for="fail-only"]{outline:3px solid var(--link);outline-offset:3px}
#all-checks:checked~.note-all,#fail-only:checked~.note-fail{display:block}#fail-only:checked~.table-shell tr[data-result]:not([data-result="FAIL"]){display:none}
.table-shell{margin-top:12px;border:1px solid var(--line);border-radius:8px;overflow:hidden}table{width:100%;border-collapse:collapse;table-layout:fixed;text-align:left;font-size:14px}th{font-weight:600;background:var(--field);padding:12px 16px;border-bottom:1px solid var(--line);font-size:12px}td{padding:15px 16px;border-bottom:1px solid var(--line);vertical-align:top;overflow-wrap:anywhere}tr:last-child td{border-bottom:0}.evidence-table th:first-child{width:65%}.evidence-table th:nth-child(2){width:19%}.evidence-table th:nth-child(3){width:16%}.operation-name{font-weight:600;margin:0;line-height:1.45}.operation-meta{display:block;font-size:12px;color:var(--muted);margin-top:6px}.check-id{display:block;font-size:10px;color:var(--muted);margin-top:4px;overflow-wrap:anywhere}.classification{display:block;font-size:11px;font-weight:400;color:var(--muted);margin-top:5px}.result{font-weight:700;font-size:12px}.result:before{content:'●';font-size:8px;margin-right:5px}.duration{font-size:11px;color:var(--muted)}td small{display:block}.empty-note{font-size:14px;padding:14px 16px;background:var(--field);border-radius:6px;margin-top:12px;display:none}#fail-only:checked~.empty-fail,#all-checks:checked~.empty-all{display:block}
details{margin:16px 0;border:1px solid var(--line);border-radius:7px;background:white}summary{padding:13px 16px;cursor:pointer;font-weight:600;font-size:14px;min-height:48px}details[open] summary{border-bottom:1px solid var(--line)}details dl,details pre,details h3{margin:16px}dl{display:grid;grid-template-columns:145px minmax(0,1fr);font-size:13px;gap:8px 18px}dt{color:var(--muted)}dd{margin:0;min-width:0}ul.limits{padding-left:20px;font-size:13px;max-width:80ch}ul.limits li{margin:7px 0}footer{border-top:1px solid var(--line);margin-top:28px;padding-top:18px;font-size:12px;color:var(--muted)}.scope-heading{margin-top:30px}
.pair{display:grid;grid-template-columns:1fr 1fr;margin:22px 0;border:1px solid var(--line);border-radius:8px;overflow:hidden}.pair article{padding:22px}.pair article+article{border-left:1px solid var(--line)}.pair .verdict{margin:0 0 12px}.pair h2{margin:0 0 12px;font-size:19px}.pair p{margin:8px 0;font-size:14px}.pair article>a{display:inline-flex;align-items:center;min-height:44px;margin-top:8px}.comparison th:first-child{width:58%}.comparison th:not(:first-child){width:21%}.comparison td small{color:var(--muted);font-size:11px;margin-top:5px}.comparison .result{font-size:12px}.comparison td{padding:13px 14px}.source-note{font-size:13px;color:var(--muted)}
@media(max-width:760px){main{margin:0;padding:20px 18px;border:0;border-radius:0}header{align-items:flex-start;display:block}nav{margin-top:12px;gap:6px;font-size:12px}nav a{padding:6px 8px}h1{font-size:27px;max-width:28ch}.facts{gap:8px 16px}.stages{grid-template-columns:repeat(3,minmax(0,1fr));row-gap:12px;margin-top:20px}.stages label{padding:7px 6px;min-height:80px}.stages b{font-size:12px}.stages small{font-size:10px}.stage-number{margin-bottom:5px}.evidence-toolbar{align-items:stretch;gap:12px}.evidence-toolbar h2{font-size:19px}.filters{width:100%}.filters label{flex:1;font-size:12px;padding:8px 9px}th,td{padding:12px 9px}.evidence-table th:first-child{width:59%}.evidence-table th:nth-child(2){width:21%}.evidence-table th:nth-child(3){width:20%}.operation-name{font-size:13px}.operation-meta{font-size:11px}.result{font-size:10px}.classification{font-size:10px}.check-id{font-size:9px}td code{font-size:11px}.finding{padding:13px 14px}.finding p{font-size:13px}dl{grid-template-columns:1fr;gap:3px}dd{margin-bottom:10px}.pair{grid-template-columns:1fr}.pair article+article{border-left:0;border-top:1px solid var(--line)}.comparison th:first-child{width:52%}.comparison th:not(:first-child){width:24%}.comparison td{padding:10px 8px;font-size:12px}.comparison .result{font-size:10px}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
@media print{body{background:white}main{margin:0;max-width:none;border:0;padding:12px}nav,.filters,.filter-input,.view-note,.skip-link{display:none!important}tr[data-result]{display:table-row!important}details{break-inside:avoid}a{color:inherit}h2{break-after:avoid}.stages label{cursor:default}}
#stage-baseline:checked~.table-shell tr[data-stage]:not([data-stage="baseline"]){display:none}
#stage-baseline:checked~.stages label[for="stage-baseline"]{background:var(--field);box-shadow:inset 0 0 0 1px var(--link)}
#stage-baseline:focus-visible~.stages label[for="stage-baseline"]{outline:3px solid var(--link);outline-offset:3px}
#stage-baseline:checked~.note-baseline,#stage-baseline:checked~.empty-baseline{display:block}
#stage-migration:checked~.table-shell tr[data-stage]:not([data-stage="migration"]){display:none}
#stage-migration:checked~.stages label[for="stage-migration"]{background:var(--field);box-shadow:inset 0 0 0 1px var(--link)}
#stage-migration:focus-visible~.stages label[for="stage-migration"]{outline:3px solid var(--link);outline-offset:3px}
#stage-migration:checked~.note-migration,#stage-migration:checked~.empty-migration{display:block}
#stage-target:checked~.table-shell tr[data-stage]:not([data-stage="target"]){display:none}
#stage-target:checked~.stages label[for="stage-target"]{background:var(--field);box-shadow:inset 0 0 0 1px var(--link)}
#stage-target:focus-visible~.stages label[for="stage-target"]{outline:3px solid var(--link);outline-offset:3px}
#stage-target:checked~.note-target,#stage-target:checked~.empty-target{display:block}
#stage-rollout:checked~.table-shell tr[data-stage]:not([data-stage="rollout"]){display:none}
#stage-rollout:checked~.stages label[for="stage-rollout"]{background:var(--field);box-shadow:inset 0 0 0 1px var(--link)}
#stage-rollout:focus-visible~.stages label[for="stage-rollout"]{outline:3px solid var(--link);outline-offset:3px}
#stage-rollout:checked~.note-rollout,#stage-rollout:checked~.empty-rollout{display:block}
#stage-mixed:checked~.table-shell tr[data-stage]:not([data-stage="mixed"]){display:none}
#stage-mixed:checked~.stages label[for="stage-mixed"]{background:var(--field);box-shadow:inset 0 0 0 1px var(--link)}
#stage-mixed:focus-visible~.stages label[for="stage-mixed"]{outline:3px solid var(--link);outline-offset:3px}
#stage-mixed:checked~.note-mixed,#stage-mixed:checked~.empty-mixed{display:block}
#stage-app_rollback:checked~.table-shell tr[data-stage]:not([data-stage="app_rollback"]){display:none}
#stage-app_rollback:checked~.stages label[for="stage-app_rollback"]{background:var(--field);box-shadow:inset 0 0 0 1px var(--link)}
#stage-app_rollback:focus-visible~.stages label[for="stage-app_rollback"]{outline:3px solid var(--link);outline-offset:3px}
#stage-app_rollback:checked~.note-app_rollback,#stage-app_rollback:checked~.empty-app_rollback{display:block}
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
            f'<title>{esc(title)}</title><style>{STYLE}</style></head><body><a class="skip-link" href="#main-content">Skip to report</a><main id="main-content">{body}'
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
    old_failed = any(c.get('status') == 'FAIL' and c.get('id') in {'old_read', 'old_write', 'rollback_read', 'rollback_new_data'} for c in failures)
    if migration_passed and old_failed:
        return 'The migration passed. Old-version requests failed.'
    return 'Application compatibility checks failed.' if failures else 'Review the recorded acceptance evidence.'


def html_report(report):
    checks = report.get('checks', [])
    failed = [c for c in checks if c.get('status') == 'FAIL']
    skipped = [c for c in checks if c.get('status') == 'SKIP']
    passed = sum(c.get('status') == 'PASS' for c in checks)
    scenario = report['scenario']
    navigation = (f'<a href="{quote(str(scenario), safe="")}.json" download>JSON evidence</a>'
                  f'<a href="{quote(str(scenario), safe="")}.md" download>Markdown</a>'
                  + ('<a href="comparison.html">Compare candidates</a>' if scenario in {'breaking', 'expand'} else ''))
    body = '<header><div><p><strong>Migration acceptance</strong></p><p class="muted">' + esc(report.get('workload', 'customer-reference')) + '<br>Commit <code title="' + esc(report['commit']) + '">' + esc(report['commit'][:12]) + '</code></p></div><nav aria-label="Report files">' + navigation + '</nav></header>'
    body += '<div class="hero">' + badge(report['verdict']) + '<h1>' + esc(introduction(report)) + '</h1>'
    body += '<p class="muted">Recorded evidence for <strong>' + esc(scenario) + '</strong>. This result covers the declared probes and fixture.</p></div>'
    if report.get('coverage'):
        body += '<p class="muted"><strong>Coverage:</strong> one mapped string CRUD workflow. Unmapped fields, derived values and other business invariants are not checked.</p>'
    body += f'<div class="facts"><span><strong>{passed}/{len(checks)}</strong> checks passed</span><span><strong>{len(failed)}</strong> failed</span><span><strong>{len(skipped)}</strong> skipped</span><span>Execution: <strong>{"complete" if report.get("completed") else "incomplete"}</strong></span><span>Cleanup: <strong>{"complete" if report.get("cleanup_ok") else "unconfirmed"}</strong></span></div>'
    # One native radio group filters by result OR execution phase. No script is
    # needed to expose passing setup/rollback probes from a failed-only view.
    body += '<fieldset class="check-region"><legend class="sr-only">Filter operation evidence by result or execution phase</legend>'
    selected = 'fail-only' if failed else 'all-checks'
    for key in ('all-checks', 'fail-only', *('stage-' + stage for stage, _ in STAGES)):
        body += f'<input class="filter-input" type="radio" name="check-filter" id="{key}" aria-controls="operation-table"' + (' checked' if key == selected else '') + '>'
    body += '<ol class="stages" aria-label="Acceptance sequence; select a phase to inspect its checks">'
    groups = {}
    for number, (stage, label) in enumerate(STAGES, 1):
        group = [c for c in checks if c.get('stage') == stage]
        groups[stage] = group
        bad = sum(c.get('status') == 'FAIL' for c in group)
        not_run = sum(c.get('status') == 'SKIP' for c in group)
        status = 'FAIL' if bad else 'SKIP' if not_run else 'PASS' if group else 'NOT RUN'
        description = f'{bad} failed / {len(group)} checks' if bad else f'{len(group)-not_run} passed' if group else 'Not run'
        if not_run:
            description += f' / {not_run} skipped'
        body += f'<li class="{tone(status)}"><label for="stage-{stage}"><span class="stage-number" aria-hidden="true">{number}</span><b>{label}</b><small>{esc(description)}</small><span class="sr-only">Inspect {label} checks</span></label></li>'
    body += '</ol>'
    if report.get('verdict') == 'INCONCLUSIVE' or not report.get('completed') or not report.get('cleanup_ok'):
        for issue in troubleshooting(report):
            body += '<aside class="finding neutral"><h3>' + esc(issue['title']) + '</h3><p>' + esc(issue['detail']) + '</p><ul>'
            body += ''.join('<li>' + esc(action) + '</li>' for action in issue['actions']) + '</ul></aside>'
    elif failed:
        first = failed[0]
        body += '<aside class="finding"><h3>First recorded failure</h3><p><strong>' + esc(first['operation']) + '</strong> / ' + esc(first['version']) + '</p>'
        if first.get('sqlstate') == '42703':
            body += '<p>SQLSTATE <code>42703</code>: an application requested a column absent from this schema. Review the old/new field mappings and preserve required fields during overlap.</p>'
        else:
            body += '<p>Inspect the failed operation and its classification before changing the candidate.</p>'
        body += '</aside>'
    body += '<div class="evidence-toolbar"><h2 id="checks-heading">Operation evidence</h2><div class="filters">'
    body += f'<label for="all-checks">All checks ({len(checks)})</label><label for="fail-only">Failures ({len(failed)})</label></div></div>'
    body += '<p class="view-note note-all">Showing every recorded check, including setup and restart. Select a phase above to narrow the evidence.</p>'
    body += '<p class="view-note note-fail">Showing failed checks. Select a phase above to inspect its passing and failing operations.</p>'
    for stage, label in STAGES:
        body += f'<p class="view-note note-{stage}">Showing {esc(label)}: {len(groups[stage])} recorded checks. Select All checks to restore the complete run.</p>'
        if not groups[stage]:
            body += f'<p class="empty-note empty-{stage}">No {esc(label)} checks were recorded. This phase is not proven by this run.</p>'
    if not failed:
        body += '<p class="empty-note empty-fail">No failed checks were recorded. Check execution and cleanup status before interpreting this result.</p>'
    if not checks:
        body += '<p class="empty-note empty-all">No operation checks were recorded. Read the setup and cleanup evidence below; this is not a successful compatibility run.</p>'
    body += '<div class="table-shell"><table class="evidence-table" id="operation-table"><caption class="sr-only">Recorded operation evidence. The selected result or phase filter changes visible rows.</caption><thead><tr><th scope="col">Operation</th><th scope="col">Result</th><th scope="col">SQL<wbr>STATE</th></tr></thead><tbody>'
    labels = dict(STAGES)
    for c in checks:
        status = c.get('status', 'UNKNOWN')
        body += f'<tr data-result="{esc(status)}" data-stage="{esc(c["stage"])}" id="check-{quote(c["id"], safe="")}"><td><p class="operation-name">{esc(c["operation"])}</p><span class="operation-meta">{esc(labels.get(c["stage"], c["stage"]))} / {esc(c["version"])}</span><small class="check-id">{esc(c["id"])}</small>'
        if status == 'SKIP' and c.get('reason_code') == 'create_not_acknowledged':
            body += '<small class="operation-meta">Not executed: new_write did not acknowledge a committed create.</small>'
        body += '</td><td>' + result(status)
        if c.get('failure_kind'):
            classification = {'compatibility': 'Compatibility', 'infrastructure_or_unknown': 'Infrastructure or unknown', 'dependency': 'Not run'}.get(c['failure_kind'], c['failure_kind'])
            body += '<small class="classification">' + esc(classification) + '</small>'
        body += '</td><td><code>' + esc(c.get('sqlstate') or '—') + '</code></td></tr>'
    body += '</tbody></table></div></fieldset>'
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
    if report.get('error_context') or report.get('cleanup_evidence'):
        evidence = {key: report[key] for key in ('error_context', 'cleanup_evidence') if key in report}
        body += '<details><summary>Failure context and cleanup evidence</summary><pre>' + esc(json.dumps(evidence, indent=2)) + '</pre></details>'
    body += '<h2 class="scope-heading">What this run covers</h2><ul class="limits">' + ''.join('<li>' + esc(v) + '</li>' for v in report.get('limitations', [])) + '</ul>'
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
