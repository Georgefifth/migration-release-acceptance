"""Render the same deterministic evidence in machine and human readable forms."""
import re
import json
from pathlib import Path
from .report_ui import html_report, write_comparison
from .diagnostics import troubleshooting


def markdown(report):
    lines = [f"# Migration acceptance: {report['verdict']}", '',
             f"Scenario: `{report['scenario']}` · Run: `{report['run_id']}`", '',
             f"Commit: `{report['commit']}`", '',
             f"Transport: {report.get('transport', 'unspecified')}", '',
             f"Workload: {report.get('workload', 'customer-reference')}", '',
             f"Fixture SHA-256: `{report['fixture_sha256']}`", '',
             '| Stage | App | Operation | Result | SQLSTATE |',
             '|---|---|---|---|---|']
    for c in report['checks']:
        lines.append(f"| {c['stage']} | {c['version']} | {c['operation']} | "
                     f"{c['status']} | {c.get('sqlstate') or '—'} |")
        if c.get('status') == 'SKIP' and c.get('reason_code') == 'create_not_acknowledged':
            lines.append('| | | Not executed: new_write did not acknowledge a committed create. | | |')
    if report.get('coverage'):
        lines += ['', 'Coverage: one mapped string CRUD workflow. Unmapped fields, derived values and other business invariants are not checked.']
    if report.get('provenance'):
        lines += ['', 'Upstream provenance: `' + json.dumps(report['provenance'], sort_keys=True) + '`']
    lines += ['', '## Scope and limitations', '']
    lines += ['- ' + item for item in report['limitations']]
    if report.get('error'):
        lines += ['', 'Execution error: ' + json.dumps(report['error'])]
    for issue in troubleshooting(report):
        lines += ['', '## ' + issue['title'], '', issue['detail'], '']
        lines += ['- ' + action for action in issue['actions']]
    if report.get('cleanup_evidence'):
        lines += ['', 'Cleanup evidence: `' + json.dumps(report['cleanup_evidence'], sort_keys=True) + '`']
    return '\n'.join(lines) + '\n'


def write_reports(report, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    stem = report['scenario']
    if not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', stem):
        raise ValueError('Invalid report scenario filename')
    (output / f'{stem}.json').write_text(json.dumps(report, indent=2) + '\n')
    md = markdown(report)
    (output / f'{stem}.md').write_text(md)
    (output / f'{stem}.html').write_text(html_report(report))
    write_comparison(output)


def load_report(path):
    """Validate shape before rendering; never turn rendering into release approval."""
    def reject_constant(_value):
        raise ValueError('Non-standard JSON constant')

    with Path(path).open() as stream:
        report = json.load(stream, parse_constant=reject_constant)
    if not isinstance(report, dict):
        raise ValueError('Expected a report object')
    for key in ('scenario', 'verdict', 'run_id', 'commit', 'fixture_sha256'):
        if not isinstance(report.get(key), str) or not report[key]:
            raise ValueError('Required report identity is missing')
    if not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', report['scenario']):
        raise ValueError('Invalid report scenario filename')
    if report['verdict'] not in {'GO_WITHIN_SCOPE', 'BLOCK', 'INCONCLUSIVE'}:
        raise ValueError('Unsupported recorded verdict')
    if any(not isinstance(report.get(key), bool) for key in ('completed', 'cleanup_ok')):
        raise ValueError('Execution and cleanup evidence is required')
    if not isinstance(report.get('limitations'), list) or not all(
            isinstance(item, str) for item in report['limitations']):
        raise ValueError('Scope limitations are required')
    if not isinstance(report.get('checks'), list):
        raise ValueError('Expected operation evidence')
    for check in report['checks']:
        if not isinstance(check, dict) or any(not isinstance(check.get(key), str)
                for key in ('id', 'stage', 'version', 'operation', 'status')):
            raise ValueError('Invalid operation evidence')
        if check['status'] not in {'PASS', 'FAIL', 'SKIP'}:
            raise ValueError('Unsupported operation status')
        if check['status'] == 'SKIP' and (check.get('depends_on') != 'new_write'
                or check.get('reason_code') != 'create_not_acknowledged'
                or check['id'] != 'rollback_new_data'):
            raise ValueError('Invalid skipped-operation evidence')
        state = check.get('sqlstate')
        if state is not None and (not isinstance(state, str) or not re.fullmatch(r'[0-9A-Z]{5}', state)):
            raise ValueError('Invalid SQLSTATE evidence')
    return report


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description='Rebuild offline acceptance views from existing JSON evidence. No database connection is made.')
    parser.add_argument('reports', type=Path, nargs='+', help='Existing acceptance JSON files')
    parser.add_argument('--output', type=Path, required=True, help='Directory for rebuilt evidence and views')
    args = parser.parse_args(argv)
    try:
        reports = [load_report(path) for path in args.reports]
        scenarios = [report['scenario'] for report in reports]
        if len(scenarios) != len(set(scenarios)):
            raise ValueError('Use separate output directories for multiple runs of the same candidate')
    except (OSError, ValueError) as exc:
        # JSON parser messages can quote data. Only print our own validation text.
        message = 'Cannot read valid report evidence' if isinstance(exc, (OSError, json.JSONDecodeError, UnicodeError)) else str(exc)
        parser.exit(2, message + '.\n')
    try:
        for report in reports:
            write_reports(report, args.output)
    except OSError:
        parser.exit(2, 'Cannot write report output.\n')
    print('Created offline reports. Rendering does not approve a release.')
    if {'breaking', 'expand'}.issubset(scenarios):
        print(args.output / 'comparison.html')
    else:
        for scenario in scenarios:
            print(args.output / (scenario + '.html'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
