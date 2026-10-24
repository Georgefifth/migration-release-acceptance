"""Install a built wheel and exercise it from an owned downstream test project."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import socket
import subprocess
import tempfile
import venv
import zipfile

ROOT = Path(__file__).resolve().parent.parent


def command(args, directory, environment, expected=0, timeout=180):
    process = subprocess.Popen(args, cwd=directory, env=environment,
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               text=True, start_new_session=True)
    try:
        stdout, _ = process.communicate(timeout=timeout)
        if process.returncode != expected:
            raise RuntimeError('Distribution verification command returned an unexpected status')
        return stdout
    except BaseException:
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(process.pid, sig)
                process.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                pass
        raise
    finally:
        process.stdout.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel', type=Path, help='Specific reviewed wheel; default requires one wheel in dist/')
    parser.add_argument('--output', type=Path, default=ROOT / 'reports/wheel-contract',
                        help='Fresh evidence directory for this verification run')
    args = parser.parse_args()
    if not os.environ.get('DATABASE_URL') or os.environ.get('ACCEPTANCE_DISPOSABLE_DB') != 'yes':
        raise RuntimeError('A disposable database is required for the wheel contract test')
    wheels = [args.wheel.resolve()] if args.wheel else list((ROOT / 'dist').glob('*.whl'))
    if len(wheels) != 1:
        raise RuntimeError('Build exactly one wheel in dist before verification')
    wheel = wheels[0]
    wheel_sha = hashlib.sha256(wheel.read_bytes()).hexdigest()
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError('Preserve previous wheel evidence; choose a fresh --output directory')
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='acceptance-downstream-') as temporary:
        stage = Path(temporary)
        downstream = stage / 'project'
        fixtures = downstream / 'fixtures'
        fixtures.mkdir(parents=True)
        with zipfile.ZipFile(wheel) as archive:
            names = archive.namelist()
            assert not any(name.startswith(('examples/', 'integrations/', 'tests/', 'reports/')) for name in names)
            assert any(name.endswith('.dist-info/licenses/LICENSE') for name in names)
            for name in ('baseline.sql', 'breaking.sql', 'expand.sql'):
                (fixtures / name).write_bytes(archive.read('acceptance/fixtures/' + name))
        (fixtures / 'missing.sql').write_text((fixtures / 'expand.sql').read_text()
            + '\nCREATE RULE discard_created AS ON INSERT TO customers DO INSTEAD NOTHING;\n')
        environment = dict(os.environ)
        environment.pop('PYTHONPATH', None)
        environment.pop('PYTHONHOME', None)
        venv_path = stage / 'venv'
        venv.EnvBuilder(with_pip=True).create(venv_path)
        python = str(venv_path / 'bin/python')
        print('Installing the wheel and declared dependencies into a fresh virtualenv.', flush=True)
        command([python, '-m', 'pip', 'install', str(wheel)], downstream, environment)
        version = command([python, '-I', '-c', 'from importlib.metadata import version; print(version("migration-release-acceptance"))'], downstream, environment).strip()
        installed = command([python, '-I', '-c', 'import acceptance; print(acceptance.__file__)'], downstream, environment).strip()
        assert Path(installed).is_relative_to(venv_path), 'The test must import the installed wheel'
        (downstream / 'project_acceptance.py').write_text('''from pathlib import Path
from acceptance.http_client import Application
from acceptance.integration import Integration
from acceptance.workload import Workload

ROOT = Path(__file__).resolve().parent

def integration():
    return Integration(
        application_factory=Application,
        workload=Workload(name="installed-wheel-reference", fixtures=ROOT / "fixtures",
                          provenance={"application": "bundled synthetic HTTP reference"}),
        candidates={"rename-contact": ROOT / "fixtures/breaking.sql",
                    "contact-storage": ROOT / "fixtures/expand.sql",
                    "missing-record": ROOT / "fixtures/missing.sql"})
''')
        # Runtime apps inherit only test connection/identity variables, not CI tokens.
        runtime = {key: os.environ[key] for key in ('PATH', 'DATABASE_URL', 'ACCEPTANCE_DISPOSABLE_DB',
                                                   'CI_COMMIT_SHA', 'CI_PIPELINE_URL') if key in os.environ}
        check_env = {key: value for key, value in runtime.items()
                     if key not in {'DATABASE_URL', 'ACCEPTANCE_DISPOSABLE_DB'}}
        accept = str(venv_path / 'bin/migration-accept')
        review = str(venv_path / 'bin/migration-report')
        command([accept, '--integration', 'project_acceptance:integration', '--check'], downstream, check_env)
        invalid = downstream / 'invalid_acceptance.py'
        invalid.write_text('from acceptance.integration import Integration\n'
                           'from acceptance.workload import Workload\n'
                           'def wrong_factory(): raise AssertionError("Must not construct")\n'
                           'def integration(): return Integration(wrong_factory, Workload())\n')
        command([accept, '--integration', 'invalid_acceptance:integration', '--check'],
                downstream, check_env, expected=2)
        command([accept, '--integration', 'project_acceptance:integration', '--candidate', 'typo', '--check'],
                downstream, check_env, expected=2)
        print('Installed wheel: invalid factory and unknown checked candidate rejected without a database')
        # Also exercise the installed default package-data paths without any DB.
        command([python, '-c', 'from acceptance.integration import Integration, validate; from acceptance.workload import Workload; from acceptance.http_client import Application; validate(Integration(Application, Workload()))'], downstream, check_env)
        runs = []
        for candidate, status, verdict in [('rename-contact', 1, 'BLOCK'), ('contact-storage', 0, 'GO_WITHIN_SCOPE')]:
            text = command([accept, '--integration', 'project_acceptance:integration', '--candidate', candidate,
                            '--output', str(output)], downstream, runtime, expected=status)
            report = json.loads(text.split('ACCEPTANCE_REPORT_BEGIN\n', 1)[1].split('\nACCEPTANCE_REPORT_END', 1)[0])
            assert report['scenario'] == candidate and report['verdict'] == verdict
            assert report['completed'] and report['cleanup_ok'] and len(report['checks']) == 16
            passed = sum(c['status'] == 'PASS' for c in report['checks'])
            assert passed == (8 if status else 16)
            runs.append(dict(candidate=candidate, verdict=verdict, exit_code=status,
                             run_id=report['run_id'], passed=passed, cleanup_ok=True))
            print(f'Installed wheel: {candidate} => {verdict}; {passed}/16 PASS; cleanup verified')
        text=command([accept,'--integration','project_acceptance:integration','--candidate','missing-record',
                      '--output',str(output)],downstream,runtime,expected=1)
        missing=json.loads(text.split('ACCEPTANCE_REPORT_BEGIN\n',1)[1].split('\nACCEPTANCE_REPORT_END',1)[0])
        assert missing['completed'] and missing['cleanup_ok'] and missing['verdict']=='BLOCK'
        assert any(c.get('failure_reason')=='record_missing' for c in missing['checks'])
        new_write=next(c for c in missing['checks'] if c['id']=='new_write')
        rollback=next(c for c in missing['checks'] if c['id']=='rollback_new_data')
        assert new_write['write_acknowledged'] is True and rollback['status']=='FAIL'
        command([review,str(output/'missing-record.json'),'--output',str(output/'offline-missing')],downstream,check_env)
        print('Installed wheel: ignored insert => BLOCK; typed record_missing retained and real rollback read attempted')
        with socket.socket() as reserved:
            reserved.bind(('127.0.0.1', 0))
            unavailable = dict(runtime, DATABASE_URL=f'postgresql://acceptance:synthetic@127.0.0.1:{reserved.getsockname()[1]}/acceptance')
            text = command([accept, '--integration', 'project_acceptance:integration', '--candidate', 'contact-storage',
                            '--output', str(output / 'database-unavailable')], downstream, unavailable, expected=2)
            failed = json.loads(text.split('ACCEPTANCE_REPORT_BEGIN\n', 1)[1].split('\nACCEPTANCE_REPORT_END', 1)[0])
            assert failed['verdict'] == 'INCONCLUSIVE' and not failed['checks']
            assert failed['error_context']['phase'] == 'database_connection'
            assert failed['cleanup_evidence']['schema_state'] == 'not_requested'
            assert 'The disposable database connection failed.' in text
            assert 'postgresql://' not in text
            print('Installed wheel: unavailable database => INCONCLUSIVE/exit 2; bounded guidance verified')
        # Copy only the reviewed synthetic HTTP mutation fixtures, not the
        # acceptance source package. Their imports must use the installed wheel.
        test_package = downstream / 'examples'
        test_package.mkdir()
        (test_package / '__init__.py').write_text('')
        for fixture in ('verify_rollback.py', 'rollback_http_app.py'):
            shutil.copyfile(ROOT / 'examples' / fixture, test_package / fixture)
        command([python, '-m', 'examples.verify_rollback'], downstream, runtime)
        shutil.copytree(downstream / 'reports/rollback-values', output / 'rollback-values', dirs_exist_ok=True)
        print('Installed wheel: exact rollback values verified for normal, stale, corrupt, empty and failed-paired-read cases')
        command([review, str(output / 'contact-storage.json'), '--output', str(output / 'offline')], downstream, check_env)
        assert (output / 'offline/contact-storage.html').is_file()
        receipt = dict(wheel=wheel.name, wheel_sha256=wheel_sha, distribution_version=version,
                       imports_from_installed_wheel=True, source_checkout_on_pythonpath=False,
                       downstream_configuration_loaded=True, preflight_without_database=True,
                       invalid_factory_and_checked_candidate_rejected=True,
                       bundled_fixtures_verified=True, offline_render_without_database=True,
                       unavailable_database_exit_2_and_guidance_verified=True,
                       rollback_value_contract_verified=True,
                       missing_record_protocol_verified=True,
                       runs=runs, independent_customer_validation=False)
        (output / 'verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
        print('Wheel contract verified from a separate generated project; this is a synthetic integration test.')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Installed distribution verification failed; inspect the build/dependency setup and any saved report evidence. No release approval was issued.') from None
