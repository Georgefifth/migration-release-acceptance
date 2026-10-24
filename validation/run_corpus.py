"""Run a frozen corpus through the public CLI in an owned disposable DB.

Never loads expected labels into the application or adapter. Runs an independent
direct-SQL oracle separately. Does not execute downloaded Python/Rust/Go code.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import time
import uuid

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/real-world-validation'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle(case, folder, dsn):
    if case['expected_verdict'] == 'CONFIG_REJECT':
        return {'status': 'NOT_APPLICABLE', 'reason': 'Configuration format test'}
    schema = 'oracle_' + uuid.uuid4().hex
    conn = psycopg.connect(dsn, autocommit=True)
    state = None
    phase = 'baseline'
    result = None
    try:
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        conn.execute(sql.SQL('SET search_path TO {},pg_catalog').format(sql.Identifier(schema)))
        conn.execute("SET statement_timeout='5s'")
        conn.execute((folder / 'baseline.sql').read_text())
        data = json.loads((folder / 'input.json').read_text())
        conn.execute(sql.SQL('INSERT INTO {} ({},{}) VALUES (%s,%s)').format(
            sql.Identifier(data['table']), sql.Identifier(data['key']),
            sql.Identifier(data['old_column'])), (100, data['values']['created']))
        phase = 'migration'
        conn.execute((folder / 'candidate.sql').read_text())
        phase = 'independent_probe'
        if case['oracle_sql']:
            row = conn.execute(case['oracle_sql']).fetchone()
            result = None if row is None else row[0] is True
    except psycopg.Error as exc:
        state = exc.sqlstate
    finally:
        conn.execute('ROLLBACK')
        conn.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(sql.Identifier(schema)))
        removed = not conn.execute('SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname=%s)', (schema,)).fetchone()[0]
        conn.close()
    expected_state = case['migration_state'] or case['oracle_state']
    matched = state == expected_state and (state is not None or result is True)
    if case['migration_state']:
        matched = matched and phase == 'migration'
    elif case['oracle_state']:
        matched = matched and phase == 'independent_probe'
    return dict(status='CONFIRMED' if matched else 'UNRESOLVED', sqlstate=state,
                phase=phase, boolean_assertion=result, schema_removed=removed)


def execute(case, folder, run_folder, dsn, sut):
    run_folder.mkdir(parents=True)
    env = {k: os.environ[k] for k in ('PATH','HOME','LANG') if k in os.environ}
    env.update(DATABASE_URL=dsn, ACCEPTANCE_DISPOSABLE_DB='yes',
               VALIDATION_INPUT=str(folder / 'input.json'), CI_COMMIT_SHA=sut)
    outputs = []
    started = time.monotonic()
    base = [sys.executable, '-m', 'acceptance.project', '--integration',
            'validation.external_adapter:integration', '--candidate', case['id']]
    for step, args in [('preflight', ['--check']), ('run', ['--output', str(run_folder)])]:
        if step == 'run' and (outputs[0]['exit_code'] != 0 or case['expected_verdict'] == 'CONFIG_REJECT'):
            break
        metrics = run_folder / (step + '-resources.json')
        command = ['/usr/bin/time','-o',str(metrics),'-f',
                   '{"wall_seconds":%e,"user_seconds":%U,"system_seconds":%S,"peak_rss_kib":%M}', *base, *args]
        proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            stdout, stderr = proc.communicate(timeout=90)
            code = proc.returncode
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            stdout, stderr = proc.communicate()
            code = 124
        (run_folder / (step + '.stdout')).write_text(stdout)
        (run_folder / (step + '.stderr')).write_text(stderr)
        # GNU time prefixes an exit-status line for expected nonzero commands.
        resource_lines = metrics.read_text().splitlines()
        resources = next((json.loads(line) for line in resource_lines if line.startswith('{')), {})
        outputs.append(dict(step=step, exit_code=code, resources=resources))
    report_file = run_folder / (case['id'] + '.json')
    report = json.loads(report_file.read_text()) if report_file.exists() else None
    observed = report['verdict'] if report else ('CONFIG_REJECT' if outputs[0]['exit_code']==2 else 'NO_REPORT')
    cleanup = None
    if report:
        schema = report['cleanup_evidence']['schema']
        with psycopg.connect(dsn) as conn:
            schema_absent = not conn.execute('SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname=%s)', (schema,)).fetchone()[0]
        alive = []
        for app in report['applications']:
            try:
                os.kill(app['pid'], 0)
                alive.append(app['pid'])
            except ProcessLookupError:
                pass
        cleanup = dict(schema_absent=schema_absent, live_recorded_pids=alive,
                       product_claim=report['cleanup_ok'])
    expected_exit = {'GO_WITHIN_SCOPE':0,'BLOCK':1,'INCONCLUSIVE':2,'CONFIG_REJECT':2}[case['expected_verdict']]
    return dict(observed_verdict=observed, verdict_matches=observed==case['expected_verdict'],
                expected_exit=expected_exit, actual_exit=outputs[-1]['exit_code'],
                exit_matches=outputs[-1]['exit_code']==expected_exit,
                steps=outputs, wall_seconds=round(time.monotonic()-started,3),
                cleanup=cleanup, failed_checks=[] if report is None else [
                    {k:c.get(k) for k in ('id','sqlstate','failure_kind')}
                    for c in report['checks'] if c['status']!='PASS'])


def benchmark(case, folder, destination):
    executable = Path(sys.executable).parent / 'squawk'
    config = destination / 'squawk.toml'
    config.write_text('')
    context = destination / 'context.sql'
    context.write_bytes(b"SET lock_timeout='2s';\nSET statement_timeout='5s';\n" + (folder/'candidate.sql').read_bytes())
    started = time.monotonic()
    completed = subprocess.run([str(executable),'--config',str(config),'--assume-in-transaction',
                                '--pg-version','16.0','--reporter','json',str(context)],
                               capture_output=True,text=True,errors='replace',timeout=30,cwd=destination)
    (destination/'squawk.stdout').write_text(completed.stdout)
    (destination/'squawk.stderr').write_text(completed.stderr)
    try:
        findings=json.loads(completed.stdout)
    except ValueError:
        findings=None
    return dict(version='2.70.0', exit_code=completed.returncode,
                wall_seconds=round(time.monotonic()-started,4),
                findings=findings, comparable_task=False,
                boundary='Same candidate SQL with matching session timeout context. Static risk warnings are not runtime compatibility verdicts.')


def main():
    global OUT
    parser=argparse.ArgumentParser()
    parser.add_argument('--split',choices=['development','holdout'],required=True)
    parser.add_argument('--label',required=True)
    parser.add_argument('--wheel',type=Path,help='Also verify an installed wheel in this owned DB')
    parser.add_argument('--corpus',type=Path,default=OUT,help='Separate frozen corpus directory; prior results stay unchanged')
    args=parser.parse_args()
    OUT=args.corpus.resolve()
    frozen=OUT/'frozen.json'
    assert digest(frozen)==(OUT/'frozen.sha256').read_text().strip(), 'Frozen plan changed'
    plan=json.loads(frozen.read_text())
    for name, expected in plan['input_sha256'].items():
        assert digest(OUT/name)==expected, 'Frozen input changed: '+name
    for name, expected in plan.get('runtime_sha256', {}).items():
        assert digest(ROOT/name)==expected, 'Frozen product runtime changed: '+name
    destination=OUT/'runs'/args.label
    if destination.exists():
        raise SystemExit('Never overwrite initial results; choose a fresh run label.')
    destination.mkdir(parents=True)
    source_hashes={str(p.relative_to(ROOT)):digest(p) for p in sorted((ROOT/'acceptance').glob('*.py'))}
    sut='working-tree:'+hashlib.sha256(json.dumps(source_hashes,sort_keys=True).encode()).hexdigest()[:16]
    environment=dict(python=sys.version, psycopg_version=psycopg.__version__, source_hashes=source_hashes,
                     adapter_sha256=digest(ROOT/'validation/external_adapter.py'),
                     plan_sha256=digest(frozen), sut=sut, split=args.split,
                     container_limits=dict(memory='512m',cpus=1,pids=128),
                     installation_attempts=[dict(python='3.14.6',result='FAILED',reason='psycopg-binary==3.2.9 has no cp314 wheel'),dict(python='3.12.3',result='SUCCESS',driver='3.2.9')])
    name='acceptance-validation-'+uuid.uuid4().hex[:12]
    password=secrets.token_urlsafe(24)
    rows=[]
    launched=False
    try:
        subprocess.run(['docker','run','--detach','--name',name,'--label','acceptance.validation=external-corpus',
                        '--memory','512m','--cpus','1','--pids-limit','128','--publish','127.0.0.1::5432',
                        '--env','POSTGRES_DB=validation','--env','POSTGRES_USER=validation',
                        '--env','POSTGRES_PASSWORD='+password,'postgres:16-alpine'],
                       check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        launched=True
        port=subprocess.check_output(['docker','port',name,'5432/tcp'],text=True).strip().rsplit(':',1)[1]
        dsn=f'postgresql://validation:{password}@127.0.0.1:{port}/validation'
        for _ in range(100):
            try:
                with psycopg.connect(dsn,connect_timeout=1) as conn:
                    environment['postgres_version']=conn.execute('SHOW server_version').fetchone()[0]
                break
            except psycopg.OperationalError:
                time.sleep(.1)
        else:
            raise RuntimeError('Owned database did not become ready')
        environment['image_id']=subprocess.check_output(['docker','inspect','--format','{{.Image}}',name],text=True).strip()
        (destination/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
        for case in plan['cases']:
            if case['split']!=args.split:
                continue
            folder=OUT/'inputs'/case['id']
            caseout=destination/case['id']
            ref=oracle(case,folder,dsn)
            result=execute(case,folder,caseout,dsn,sut)
            comp=benchmark(case,folder,caseout)
            row=dict(id=case['id'],difficulty=case['difficulty'],category=case['category'],
                     expected_verdict=case['expected_verdict'],oracle=ref,product=result,competitor=comp,
                     out_of_scope_hazard=case.get('out_of_scope_hazard',False))
            rows.append(row)
            (destination/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
            print(case['id'],case['expected_verdict'],'=>',result['observed_verdict'],
                  'oracle='+ref['status'],flush=True)
        if args.wheel:
            wheel_env={k:os.environ[k] for k in ('PATH','HOME','LANG') if k in os.environ}
            wheel_env.update(DATABASE_URL=dsn,ACCEPTANCE_DISPOSABLE_DB='yes')
            contract=subprocess.run([sys.executable,'tools/verify_distribution.py','--wheel',str(args.wheel.resolve()),
                                     '--output',str(destination/'installed-wheel')],cwd=ROOT,env=wheel_env,
                                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=240)
            (destination/'wheel.stdout').write_text(contract.stdout)
            (destination/'wheel.stderr').write_text(contract.stderr)
            environment['installed_wheel_exit']=contract.returncode
        with psycopg.connect(dsn) as conn:
            environment['remaining_owned_schemas']=conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'acceptance_%' OR nspname LIKE 'oracle_%'").fetchone()[0]
        environment['docker_stats']=subprocess.check_output(['docker','stats','--no-stream','--format',
            '{"memory":"{{.MemUsage}}","cpu":"{{.CPUPerc}}"}',name],text=True).strip()
    finally:
        if launched:
            removed=subprocess.run(['docker','rm','--force','--volumes',name],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE).returncode==0
            check=subprocess.run(['docker','inspect',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            environment['owned_container_removed']=removed and check.returncode!=0
        (destination/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
    print(dict(cases=len(rows),verdict_matches=sum(r['product']['verdict_matches'] for r in rows),
               oracles=dict(Counter(r['oracle']['status'] for r in rows))),flush=True)


if __name__=='__main__':
    main()
