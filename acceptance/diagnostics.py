"""Bounded troubleshooting guidance derived from evidence, never a new verdict."""
import re


def troubleshooting(report):
    if report.get('verdict') == 'GO_WITHIN_SCOPE' and report.get('completed') and report.get('cleanup_ok'):
        return []
    checks = report.get('checks', [])
    failed = next((c for c in checks if isinstance(c, dict) and c.get('status') == 'FAIL'), {})
    context = report.get('error_context')
    context = context if isinstance(context, dict) else {}
    check = context.get('check_id') or failed.get('id')
    failed = next((c for c in checks if isinstance(c, dict) and c.get('id') == check
                   and c.get('status') == 'FAIL'), failed)
    phase = context.get('phase')
    issues = []

    def add(code, title, detail, *actions):
        issues.append(dict(code=code, title=title, detail=detail, actions=list(actions)))

    cleanup_only = report.get('completed') and not failed and not report.get('error') and not report.get('cleanup_ok')
    if cleanup_only:
        pass
    elif phase == 'adapter_construction':
        add('adapter_setup', 'Application adapter setup did not finish.',
            'The run stopped before it could establish application compatibility.',
            'Check adapter imports, constructor arguments and the required lifecycle/HTTP methods.',
            'Keep construction side-effect free; launch owned processes only in start().')
    elif phase == 'database_connection':
        add('database_connection', 'The disposable database connection failed.',
            'No candidate SQL was executed by this run.',
            'Check that your disposable PostgreSQL service is running and reachable from this process.',
            'Verify the test database name and credentials locally; do not paste the connection URL into reports.')
    elif phase == 'schema_setup':
        add('schema_setup', 'Disposable schema setup did not finish.',
            'The run could not prepare its isolated test schema.',
            'Check connection health and whether the disposable test role can create and remove its own schema.')
    elif phase in {'baseline_setup', 'workload_initialization'} or check in {'baseline_read', 'baseline_write'}:
        add('baseline_setup', 'The old-version baseline was not established.',
            'This is not evidence that the candidate migration broke the application.',
            'Check baseline SQL, synthetic seed ID/value mapping and the old application adapter.',
            'If using an initializer, verify it targets only the assigned test schema.')
    elif check == 'migration':
        add('candidate_execution', 'Candidate SQL did not complete successfully.',
            'Old/new compatibility cannot be established until candidate execution succeeds.',
            'Inspect the recorded SQLSTATE and reviewed SQL against the synthetic baseline and PostgreSQL version.',
            'Correct the candidate or test setup and rerun; do not interpret this as a compatibility BLOCK.')
    elif check in {'applications_started', 'new_application_started', 'rollback_restart'}:
        title = {'applications_started': 'The old application did not become ready.',
                 'new_application_started': 'The new application did not become ready.',
                 'rollback_restart': 'The old application restart was not verified.'}[check]
        add('application_startup', title,
            'The required HTTP process/readiness evidence is incomplete.',
            'Check the reviewed launch command, installed app dependencies and required synthetic test environment.',
            'Verify loopback binding, database-aware health response and restart/stop behavior.')
    elif report.get('verdict') == 'BLOCK' or failed.get('failure_kind') == 'compatibility':
        add('compatibility', 'Declared application checks observed an incompatibility.',
            'These observations are limited to this workload and do not override the recorded verdict or cleanup state.',
            'Inspect the first failed operation and its SQLSTATE or value assertion.',
            'Review old/new field mappings and preserve required old-version behavior through the overlap window.')
    elif failed or phase == 'application_checks':
        add('request_incomplete', 'Application execution could not establish compatibility.',
            'A timeout or unclassified execution failure must not be treated as a proven migration defect.',
            'Check test app health, HTTP/auth/ID mapping and the recorded failing operation.',
            'Translate only known incompatibilities; keep unknown responses and server messages out of evidence.')
    else:
        add('evidence_incomplete', 'Execution evidence is incomplete.',
            'The saved result does not establish compatibility.',
            'Inspect the declared operation evidence, restore the missing setup/execution step and rerun.')

    if any(c.get('status') == 'SKIP' and c.get('reason_code') == 'create_not_acknowledged'
           for c in checks if isinstance(c, dict)):
        add('dependent_probe_skipped', 'A dependent rollback read was not executed.',
            'The new-version create did not acknowledge a committed record. The skipped read is not passing rollback evidence.',
            'Inspect new_write first, repair its failure and rerun to establish rollback reads of new data.')

    if not report.get('cleanup_ok'):
        cleanup = report.get('cleanup_evidence')
        cleanup = cleanup if isinstance(cleanup, dict) else {}
        schema = cleanup.get('schema')
        safe_schema = schema if isinstance(schema, str) and re.fullmatch(r'acceptance_[0-9a-f]{32}', schema) else None
        detail = 'The run cannot confirm that all of its owned resources were cleaned up.'
        actions = ['Check the recorded application stop, schema removal and connection-close evidence before retrying.']
        if cleanup.get('schema_state') == 'unconfirmed' and safe_schema:
            detail += ' Owned test schema: ' + safe_schema + '.'
            actions.append('Inspect that exact schema in the disposable database; remove it only after confirming ownership and that no test process still uses it.')
        if cleanup.get('applications_stopped') is False:
            actions.append('Inspect the owned application processes and repair stop(); do not kill processes from an old report without checking their current identity.')
        add('cleanup_unconfirmed', 'Owned-resource cleanup is unconfirmed.', detail, *actions)
    return issues


def summary_lines(report):
    lines = ['Result: ' + report['verdict']]
    for issue in troubleshooting(report):
        lines.append('Check: ' + issue['title'])
        lines.extend('  - ' + action for action in issue['actions'])
    return lines
