"""Render the same deterministic evidence in machine and human readable forms."""
import html
import json
from pathlib import Path


def markdown(report):
    lines = [f"# Migration acceptance: {report['verdict']}", '',
             f"Scenario: `{report['scenario']}` · Run: `{report['run_id']}`", '',
             f"Commit: `{report['commit']}`", '',
             f"Fixture SHA-256: `{report['fixture_sha256']}`", '',
             '| Stage | App | Operation | Result | SQLSTATE |',
             '|---|---|---|---|---|']
    for c in report['checks']:
        lines.append(f"| {c['stage']} | {c['version']} | {c['operation']} | "
                     f"{c['status']} | {c.get('sqlstate') or '—'} |")
    lines += ['', '## Scope and limitations', '']
    lines += ['- ' + item for item in report['limitations']]
    if report.get('error'):
        lines += ['', 'Execution error: ' + json.dumps(report['error'])]
    return '\n'.join(lines) + '\n'


def write_reports(report, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    stem = report['scenario']
    (output / f'{stem}.json').write_text(json.dumps(report, indent=2) + '\n')
    md = markdown(report)
    (output / f'{stem}.md').write_text(md)
    # Escape all evidence. A report may eventually include untrusted repository data.
    rows = ''.join('<tr>' + ''.join('<td>' + html.escape(str(value)) + '</td>' for value in
                   (c['stage'], c['version'], c['operation'], c['status'], c.get('sqlstate') or '—'))
                   + '</tr>' for c in report['checks'])
    limitations = ''.join('<li>' + html.escape(x) + '</li>' for x in report['limitations'])
    error = html.escape(json.dumps(report.get('error', {})))
    document = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Migration acceptance evidence</title><style>
body{font:16px/1.6 system-ui;margin:40px auto;padding:0 24px;max-width:1050px;color:#18212c}
h1{font-size:30px}table{border-collapse:collapse;width:100%}td,th{padding:10px;text-align:left;border-bottom:1px solid #d6dce2}
code{overflow-wrap:anywhere}small{color:#526373}</style>'''
    document += f"<h1>{html.escape(report['verdict'])}</h1>"
    document += f"<p>Scenario: {html.escape(stem)} · Run: {html.escape(report['run_id'])}</p>"
    document += f"<p>Commit: <code>{html.escape(report['commit'])}</code></p>"
    document += '<table><thead><tr><th>Stage</th><th>App</th><th>Operation</th><th>Result</th><th>SQLSTATE</th></tr></thead><tbody>'
    document += rows + '</tbody></table><h2>Scope and limitations</h2><ul>' + limitations + '</ul>'
    document += f'<small>Execution error: {error}</small></html>'
    (output / f'{stem}.html').write_text(document)
