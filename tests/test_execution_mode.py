"""Explicit execution mode boundaries and evidence identity."""
import contextlib
from dataclasses import replace
import io
import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from acceptance.integration import ConfigurationError, Integration, validate
from acceptance.project import main
from acceptance.runner import run
from acceptance.report import load_report, write_reports
from acceptance.report_ui import comparison_gap
from acceptance.workload import Workload
from test_report_ui import run_report


class ExecutionModeTests(unittest.TestCase):
    def test_invalid_modes_rejected_before_factory_or_database(self):
        def forbidden(*args):
            raise AssertionError('Must not construct')
        for value in (None, 0, 1, 'false', [], {}):
            with self.subTest(value=value), patch('psycopg.connect', side_effect=AssertionError('No database')):
                with self.assertRaisesRegex(ConfigurationError, 'boolean'):
                    validate(Integration(forbidden, Workload(), candidate_transactional=value))
                with self.assertRaisesRegex(ValueError, 'boolean'):
                    run('expand', 'private', application_factory=forbidden, migration_transactional=value)

    def test_public_entry_passes_reviewed_false_and_preflight_explains_mode(self):
        from examples.project_acceptance import integration
        config=replace(integration(), candidate_transactional=False)
        output=io.StringIO()
        with patch('acceptance.project.load', return_value=validate(config)), patch('acceptance.project.run') as execute, contextlib.redirect_stdout(output):
            self.assertEqual(main(['--integration','examples.project_acceptance:integration','--check']),0)
            execute.assert_not_called()
            self.assertIn('disabled',output.getvalue())
            execute.return_value={'scenario':'expand','verdict':'INCONCLUSIVE'}
            with patch.dict(os.environ,DATABASE_URL='synthetic',ACCEPTANCE_DISPOSABLE_DB='yes'), patch('acceptance.project.write_reports'):
                self.assertEqual(main(['--integration','examples.project_acceptance:integration','--candidate','expand']),2)
            self.assertIs(execute.call_args.kwargs['migration_transactional'],False)

    def test_mode_is_preserved_and_mismatched_evidence_cannot_compare(self):
        left,right=run_report('breaking'),run_report()
        self.assertIsNone(comparison_gap(left,right)) # Historical reports default to wrapped.
        right['migration_transactional']=False
        self.assertIn('wrappers differ',comparison_gap(left,right))
        with tempfile.TemporaryDirectory() as temporary:
            write_reports(right,temporary)
            path=Path(temporary)/'expand.json'
            self.assertIs(load_report(path)['migration_transactional'],False)
            self.assertIn('Candidate transaction wrapper: disabled',(Path(temporary)/'expand.md').read_text())
            self.assertIn('Candidate transaction wrapper',(Path(temporary)/'expand.html').read_text())
            right['migration_transactional']='false'
            write_reports(right,temporary)
            with self.assertRaisesRegex(ValueError,'execution mode'):
                load_report(path)
        self.assertIn('invalid',comparison_gap(left,right))
