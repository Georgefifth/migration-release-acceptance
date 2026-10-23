import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from acceptance.report import main
from test_report_ui import run_report


class OfflineReportTests(unittest.TestCase):
    def test_blocked_and_passing_evidence_roundtrip_without_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            left = run_report('breaking')
            left['verdict'] = 'BLOCK'
            left['checks'][5].update(status='FAIL', sqlstate='42703')
            right = run_report()
            for name, report in [('left', left), ('right', right)]:
                (root / (name+'.json')).write_text(json.dumps(report))
            with contextlib.redirect_stdout(io.StringIO()):
                result = main([str(root/'left.json'), str(root/'right.json'), '--output', str(root/'out')])
            self.assertEqual(result, 0)  # Rendering success, not a GO verdict.
            self.assertEqual(json.loads((root/'out/breaking.json').read_text()), left)
            self.assertEqual(json.loads((root/'out/expand.json').read_text()), right)
            self.assertIn('BLOCK', (root/'out/comparison.html').read_text())

    def test_invalid_second_input_leaves_no_partial_output_or_data_leak(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'valid.json').write_text(json.dumps(run_report()))
            (root/'bad.json').write_text('{"private": sensitive-value}')
            error = io.StringIO()
            with contextlib.redirect_stderr(error), self.assertRaises(SystemExit) as caught:
                main([str(root/'valid.json'), str(root/'bad.json'), '--output', str(root/'out')])
            self.assertEqual(caught.exception.code, 2)
            self.assertFalse((root/'out').exists())
            self.assertNotIn('sensitive-value', error.getvalue())

    def test_duplicate_candidate_runs_are_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'run.json').write_text(json.dumps(run_report()))
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main([str(root/'run.json'), str(root/'run.json'), '--output', str(root/'out')])
            self.assertFalse((root/'out').exists())


if __name__ == '__main__':
    unittest.main()
