"""Runnable project-local adapter example using the synthetic reference app."""
import sys

from acceptance.http_client import Application
from acceptance.integration import Integration
from acceptance.workload import Workload


class ProjectApplication(Application):
    def command(self, ready_file):
        # Replace this with your reviewed v1/v2 launch commands. This example
        # deliberately keeps the same synthetic app, not a real customer system.
        return [sys.executable, '-m', 'acceptance.http_app', '--version', self.version,
                '--ready-file', str(ready_file)]


def integration():
    return Integration(application_factory=ProjectApplication, workload=Workload())


def main():
    from acceptance.project import main as project_main
    return project_main(['--integration', 'examples.project_acceptance:integration',
                         '--output', 'reports/project-adapter', *sys.argv[1:]])


if __name__ == '__main__':
    raise SystemExit(main())
