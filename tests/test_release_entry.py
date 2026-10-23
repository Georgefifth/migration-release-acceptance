import contextlib
import io
import unittest
from unittest.mock import patch

from integrations.release_acceptance import main


class ReleaseEntryTests(unittest.TestCase):
    def test_real_candidate_gate_preserves_each_release_exit_code(self):
        for scenario, candidate, code in [('expand', 'item-title-storage', 0),
                                           ('breaking', 'rename-title', 1),
                                           ('expand', 'item-title-storage', 2)]:
            with self.subTest(scenario=scenario, code=code), patch('integrations.release_acceptance.project_main', return_value=code) as project:
                self.assertEqual(main(['--scenario', scenario]), code)
                self.assertEqual(project.call_args.args[0],
                                 ['--integration', 'integrations.fastapi_case:integration',
                                  '--candidate', candidate, '--output', 'reports/release'])

    def test_invalid_selection_does_not_run_an_application(self):
        with patch('integrations.release_acceptance.project_main') as project, contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            main(['--scenario', 'not-reviewed'])
        self.assertEqual(caught.exception.code, 2)
        project.assert_not_called()
