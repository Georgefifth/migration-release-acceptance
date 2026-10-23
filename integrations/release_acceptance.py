"""Run the selected real FastAPI candidate as a release gate, not a self-test."""
import argparse
from pathlib import Path

from acceptance.project import main as project_main


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', required=True, choices=['expand', 'breaking'])
    parser.add_argument('--output', type=Path, default=Path('reports/release'))
    args = parser.parse_args(argv)
    candidate = {'expand': 'item-title-storage', 'breaking': 'rename-title'}[args.scenario]
    return project_main(['--integration', 'integrations.fastapi_case:integration',
                         '--candidate', candidate, '--output', str(args.output)])


if __name__ == '__main__':
    raise SystemExit(main())
