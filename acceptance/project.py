"""Check or run a reviewed project's application/workload integration."""
import argparse
import json
import os
from pathlib import Path

from .integration import ConfigurationError, candidate_paths, load
from .report import write_reports
from .runner import run


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--integration', required=True, help='Trusted package.module:configuration_function; importing executes code')
    parser.add_argument('--check', action='store_true', help='Check configuration and fixture files without starting apps or accessing a database')
    parser.add_argument('--candidate', '--scenario', dest='scenario', help='Candidate name declared by the integration')
    parser.add_argument('--output', type=Path, default=Path('reports/project'))
    args = parser.parse_args(argv)
    if not args.check and args.scenario is None:
        parser.error('--scenario is required when running acceptance')
    try:
        config = load(args.integration)
    except ConfigurationError as exc:
        parser.exit(2, 'Configuration check failed: ' + str(exc) + '\n')
    if args.check:
        print('Configuration, baseline SQL and declared candidate files are ready.')
        print('Candidates: ' + ', '.join(candidate_paths(config)))
        print('No application or database was started by this check. The configuration itself is trusted Python code.')
        print('Runtime startup, SQL correctness and compatibility still require an acceptance run.')
        return 0
    if args.scenario not in candidate_paths(config):
        parser.exit(2, 'Unknown candidate. Run --check to list the declared candidate names.\n')
    dsn = os.environ.get('DATABASE_URL')
    if not dsn or os.environ.get('ACCEPTANCE_DISPOSABLE_DB') != 'yes':
        parser.exit(2, 'DATABASE_URL and ACCEPTANCE_DISPOSABLE_DB=yes are required for your disposable test database.\n')
    try:
        report = run(args.scenario, dsn, application_factory=config.application_factory,
                     workload=config.workload, migration_path=candidate_paths(config)[args.scenario])
        write_reports(report, args.output)
    except Exception:
        parser.exit(2, 'Acceptance could not finish or save its evidence. Check the reviewed adapter, fixtures and output directory; no release approval was issued.\n')
    print('ACCEPTANCE_REPORT_BEGIN')
    print(json.dumps(report))
    print('ACCEPTANCE_REPORT_END')
    print('Report: ' + str((args.output / (args.scenario + '.html')).resolve()))
    return {'GO_WITHIN_SCOPE': 0, 'BLOCK': 1, 'INCONCLUSIVE': 2}[report['verdict']]


if __name__ == '__main__':
    raise SystemExit(main())
