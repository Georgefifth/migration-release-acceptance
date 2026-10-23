"""Preflight boundaries, controlled errors and acceptance exit semantics."""
import contextlib
from dataclasses import replace
import io
import os
import sys
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from acceptance.integration import ConfigurationError, Integration, candidate_paths, load, validate
from acceptance.project import main
from acceptance.workload import Workload


class ProjectEntryTests(unittest.TestCase):
    def test_console_entry_loads_configuration_from_invoking_project_and_restores_path(self):
        before = sys.path[:]
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary:
            Path(temporary, 'downstream_test_configuration.py').write_text(
                'from acceptance.integration import Integration\n'
                'from acceptance.http_client import Application\n'
                'from acceptance.workload import Workload\n'
                'def integration(): return Integration(Application, Workload())\n')
            try:
                os.chdir(temporary)
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(['--integration', 'downstream_test_configuration:integration', '--check']), 0)
                self.assertEqual(sys.path, before)
            finally:
                os.chdir(previous)
                sys.modules.pop('downstream_test_configuration', None)

    def test_reference_preflight_does_not_construct_apps_or_access_database(self):
        from examples.project_acceptance import ProjectApplication
        output = io.StringIO()
        with patch.object(ProjectApplication, '__init__', side_effect=AssertionError('Do not construct')), patch('acceptance.project.run', side_effect=AssertionError('Do not run')), patch.dict(os.environ, DATABASE_URL='postgresql://private-value'), contextlib.redirect_stdout(output):
            self.assertEqual(main(['--integration', 'examples.project_acceptance:integration', '--check']), 0)
        self.assertNotIn('private-value', output.getvalue())
        self.assertIn('compatibility still require', output.getvalue())

    def test_missing_fixture_names_the_fix_before_a_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = Integration(lambda *_: None, Workload(fixtures=Path(temporary)))
            with self.assertRaisesRegex(ConfigurationError, 'baseline.sql'):
                validate(config)

    def test_single_project_candidate_does_not_require_demo_migrations(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / 'baseline.sql').write_text('SELECT 1;')
            (directory / 'reviewed-change.sql').write_text('SELECT 2;')
            config = Integration(lambda *_: None, Workload(fixtures=directory),
                                 candidates={'title-storage': directory / 'reviewed-change.sql'})
            self.assertIs(validate(config), config)
            self.assertEqual(list(candidate_paths(config)), ['title-storage'])
            with self.assertRaisesRegex(ConfigurationError, 'Candidate names'):
                validate(replace(config, candidates={'../escape': directory / 'reviewed-change.sql'}))

    def test_bad_metadata_is_not_deferred_to_report_writing(self):
        config = Integration(lambda *_: None, Workload(provenance={'bad': float('nan')}))
        with self.assertRaisesRegex(ConfigurationError, 'finite JSON'):
            validate(config)
        with self.assertRaisesRegex(ConfigurationError, 'initialize'):
            validate(replace(config, workload=Workload(initialize='not callable')))

    def test_user_configuration_errors_do_not_echo_private_values(self):
        def broken():
            raise ConfigurationError('postgresql://private-value')
        module = types.SimpleNamespace(integration=broken)
        error = io.StringIO()
        with patch('acceptance.integration.importlib.import_module', return_value=module), contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as exit:
            main(['--integration', 'reviewed.config:integration', '--check'])
        self.assertEqual(exit.exception.code, 2)
        self.assertNotIn('private-value', error.getvalue())
        self.assertIn('prepared application files', error.getvalue())

    def test_run_requires_disposable_acknowledgement(self):
        with patch.dict(os.environ, {}, clear=True), patch('acceptance.project.run') as run, contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exit:
            main(['--integration', 'examples.project_acceptance:integration', '--scenario', 'expand'])
        self.assertEqual(exit.exception.code, 2)
        run.assert_not_called()

    def test_undeclared_candidate_never_starts_acceptance(self):
        with patch('acceptance.project.run') as run, contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exit:
            main(['--integration', 'examples.project_acceptance:integration', '--candidate', 'not-declared'])
        self.assertEqual(exit.exception.code, 2)
        run.assert_not_called()

    def test_recorded_verdicts_retain_release_exit_codes(self):
        config = load('examples.project_acceptance:integration')
        for verdict, code in [('GO_WITHIN_SCOPE', 0), ('BLOCK', 1), ('INCONCLUSIVE', 2)]:
            with self.subTest(verdict=verdict), patch.dict(os.environ, DATABASE_URL='test-only', ACCEPTANCE_DISPOSABLE_DB='yes'), patch('acceptance.project.run', return_value={'scenario': 'expand', 'verdict': verdict}) as run, patch('acceptance.project.write_reports'), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(['--integration', 'examples.project_acceptance:integration', '--scenario', 'expand']), code)
                self.assertEqual(run.call_args.kwargs['workload'], config.workload)
                self.assertEqual(run.call_args.kwargs['migration_path'], config.workload.fixtures / 'expand.sql')
