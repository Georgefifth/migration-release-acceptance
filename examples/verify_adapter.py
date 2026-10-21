"""Exercise the project-local integration and fail-closed lifecycle behavior."""
import os
from pathlib import Path

from acceptance.report import write_reports
from acceptance.runner import CHECK_IDS, run
from .project_acceptance import ProjectApplication


class StartupFailure(ProjectApplication):
    def start(self):
        super().start()
        raise RuntimeError('Simulated failure after a real process starts')


def main():
    dsn = os.environ['DATABASE_URL']
    for scenario, expected in [('expand', 'GO_WITHIN_SCOPE'), ('breaking', 'BLOCK')]:
        report = run(scenario, dsn, application_factory=ProjectApplication)
        write_reports(report, Path('reports/project-adapter'))
        assert report['verdict'] == expected
        assert report['application_factory'] == 'examples.project_acceptance:ProjectApplication'
        assert len(report['checks']) == len(CHECK_IDS)
        assert report['cleanup_ok']
        print(f'Project adapter: {scenario} => {expected}; {len(CHECK_IDS)} checks')
    report = run('expand', dsn, application_factory=StartupFailure)
    write_reports(report, Path('reports/startup-failure'))
    assert report['verdict'] == 'INCONCLUSIVE'
    assert report['cleanup_ok'], 'Partially started application must be stopped and schema removed'
    assert not report['completed']
    assert report['error'] == {'kind': 'RuntimeError'}
    print('Partial-startup failure => INCONCLUSIVE; process and schema cleanup verified')


if __name__ == '__main__':
    main()
