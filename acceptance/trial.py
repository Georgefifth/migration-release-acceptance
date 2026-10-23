"""Run the reference trial with an owned disposable database; standard library only."""
import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parent.parent
IMAGE = 'postgres:16-alpine'


class TrialError(Exception):
    pass


def command(args, *, env=None, timeout=180):
    """Keep subprocess diagnostics private and stop the whole owned process group."""
    process = subprocess.Popen(args, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True, start_new_session=True)
    try:
        stdout, _ = process.communicate(timeout=timeout)
        return process.returncode, stdout.strip()
    except BaseException:
        # The worker's HTTP apps inherit this group. Never leave them listening.
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        raise
    finally:
        if process.stdout is not None:
            process.stdout.close()


def require(args, message, **kwargs):
    if command(args, **kwargs)[0]:
        raise TrialError(message)


def source_commit():
    # Do not inspect a parent checkout or label edited files with its clean SHA.
    if not (ROOT / '.git').exists() or not shutil.which('git'):
        return 'local-development'
    code, top = command(['git', 'rev-parse', '--show-toplevel'])
    if code or Path(top).resolve() != ROOT:
        return 'local-development'
    code, status = command(['git', 'status', '--porcelain', '--untracked-files=normal'])
    if code or status:
        return 'local-development'
    code, sha = command(['git', 'rev-parse', 'HEAD'])
    return sha if not code else 'local-development'


def remove_owned_container(name, trial_id):
    code, label = command(['docker', 'inspect', '--format',
                          '{{ index .Config.Labels "acceptance.trial" }}', name], timeout=15)
    if code or label != trial_id:
        return False
    return command(['docker', 'rm', '--force', '--volumes', name], timeout=30)[0] == 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check prerequisites without creating resources')
    args = parser.parse_args(argv)
    if os.name != 'posix' or sys.version_info < (3, 12):
        print('Use Python 3.12+ on Linux or macOS (including a Linux WSL environment).', file=sys.stderr)
        return 2
    if not shutil.which('docker'):
        print('Docker is missing. Install/start Docker, then rerun this command.', file=sys.stderr)
        return 2
    name = None
    started = False
    exit_code = 2
    try:
        require(['docker', 'info'], 'Docker is unavailable. Start Docker and check your user has access; no sudo is run.', timeout=15)
        require([sys.executable, '-m', 'venv', '--help'], 'Python venv is unavailable. Install your Python distribution\'s venv support.', timeout=15)
        if args.check:
            print('Prerequisites available. No database or reports created. Downloads are checked during the trial.')
            return 0
        trial_id = uuid.uuid4().hex
        name = 'acceptance-trial-' + trial_id
        output = ROOT / 'reports' / ('trial-' + trial_id)
        commit = source_commit()
        environment = dict(os.environ)
        environment.pop('DATABASE_URL', None)
        environment.pop('CI_PIPELINE_URL', None)
        environment.update(CI_COMMIT_SHA=commit, PIP_DISABLE_PIP_VERSION_CHECK='1')
        print('Preparing an isolated Python environment. First run downloads one dependency.', flush=True)
        with tempfile.TemporaryDirectory(prefix='acceptance-trial-') as temporary:
            venv = Path(temporary) / 'venv'
            require([sys.executable, '-m', 'venv', str(venv)], 'Could not create an isolated Python environment.')
            python = str(venv / 'bin/python')
            require([python, '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt')],
                    'Dependency download failed. Check access to your configured Python package index, then retry.')
            print('Starting disposable PostgreSQL 16 on a random loopback port. First run may download the image.', flush=True)
            environment['POSTGRES_PASSWORD'] = secrets.token_hex(24)
            # Mark before starting: Docker may create a container before the client is interrupted.
            started = True
            require(['docker', 'run', '--detach', '--name', name, '--label', 'acceptance.trial=' + trial_id,
                     '--publish', '127.0.0.1::5432', '--env', 'POSTGRES_PASSWORD',
                     '--env', 'POSTGRES_USER=acceptance', '--env', 'POSTGRES_DB=acceptance', IMAGE],
                    'Could not start PostgreSQL. Check Docker image-download access and available resources.', env=environment)
            code, address = command(['docker', 'port', name, '5432/tcp'], timeout=15)
            if code or not address.startswith('127.0.0.1:') or not address.split(':')[-1].isdigit():
                raise TrialError('Docker did not provide the expected loopback database port.')
            environment['DATABASE_URL'] = 'postgresql://acceptance:' + environment['POSTGRES_PASSWORD'] + '@' + address + '/acceptance'
            environment.pop('POSTGRES_PASSWORD')
            environment['ACCEPTANCE_DISPOSABLE_DB'] = 'yes'
            require([python, '-m', 'acceptance.wait_db'], 'The disposable database did not become ready.', env=environment, timeout=75)
            print('Running the unsafe and compatible reference candidates through independent HTTP apps.', flush=True)
            require([python, '-m', 'acceptance.demo', '--output', str(output)],
                    'The trial did not verify both expected outcomes. Any completed reports are retained at ' + str(output), env=environment)
            for candidate in ('breaking', 'expand'):
                report = json.loads((output / (candidate + '.json')).read_text())
                passed = sum(c['status'] == 'PASS' for c in report['checks'])
                print(f'{candidate}: {report["verdict"]}; {passed}/{len(report["checks"])} checks passed; schema/app cleanup: {report["cleanup_ok"]}')
            if commit == 'local-development':
                print('Source is unversioned or edited. Reports show individual outcomes; direct comparison is withheld. Use a clean Git checkout for comparison.')
            print('Open: ' + str(output / 'comparison.html'))
            print('Trial success verifies expected fixture outcomes, not approval of your own migration.')
            exit_code = 0
    except KeyboardInterrupt:
        print('Trial interrupted; cleaning up owned resources.', file=sys.stderr)
        exit_code = 130
    except (TrialError, OSError, subprocess.TimeoutExpired, ValueError, KeyError):
        # Only controlled messages may cross this boundary; never echo commands/DSNs.
        error = sys.exception()
        print(str(error) if isinstance(error, TrialError) else 'Trial could not complete. Check Docker, Python venv and download access, then retry.', file=sys.stderr)
    finally:
        if started:
            try:
                cleaned = remove_owned_container(name, trial_id)
            except (OSError, subprocess.TimeoutExpired):
                cleaned = False
            if cleaned:
                print('Disposable database container and its anonymous data removed.')
            else:
                print('Database container cleanup is unconfirmed. Check Docker and remove only ' + name + ' with: docker rm --force --volumes ' + name, file=sys.stderr)
                exit_code = 2
    return exit_code


if __name__ == '__main__':
    def interrupt(_signum, _frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupt)
    raise SystemExit(main())
