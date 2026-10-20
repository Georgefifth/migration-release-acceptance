import copy
import tempfile
import unittest
from pathlib import Path
from acceptance.runner import CHECK_IDS, verdict
from acceptance.report import write_reports


def complete():
    return dict(completed=True, cleanup_ok=True, checks=[
        dict(id=name, status='PASS', stage='test', version='v1', operation=name)
        for name in CHECK_IDS])


class GateTests(unittest.TestCase):
    def test_complete_evidence_only_allows_scoped_go(self):
        self.assertEqual(verdict(complete()), 'GO_WITHIN_SCOPE')

    def test_missing_or_duplicate_evidence_cannot_pass(self):
        report = complete()
        report['checks'].pop()
        self.assertEqual(verdict(report), 'INCONCLUSIVE')
        report['checks'].append(copy.deepcopy(report['checks'][0]))
        self.assertEqual(verdict(report), 'INCONCLUSIVE')

    def test_new_version_pass_cannot_hide_old_version_failure(self):
        report = complete()
        report['checks'][CHECK_IDS.index('old_read')].update(
            status='FAIL', failure_kind='compatibility', sqlstate='42703')
        self.assertEqual(verdict(report), 'BLOCK')

    def test_failed_baseline_and_migration_are_inconclusive(self):
        for name in ['baseline_read', 'baseline_write', 'migration']:
            with self.subTest(name=name):
                report = complete()
                report['checks'][CHECK_IDS.index(name)].update(
                    status='FAIL', failure_kind='compatibility')
                self.assertEqual(verdict(report), 'INCONCLUSIVE')

    def test_infrastructure_failure_does_not_claim_application_bug(self):
        report = complete()
        report['checks'][-1].update(status='FAIL', failure_kind='infrastructure_or_unknown')
        self.assertEqual(verdict(report), 'INCONCLUSIVE')

    def test_cleanup_or_incomplete_execution_cannot_pass(self):
        for key in ['completed', 'cleanup_ok']:
            report = complete()
            report[key] = False
            self.assertEqual(verdict(report), 'INCONCLUSIVE')

    def test_html_escapes_untrusted_evidence(self):
        report = complete()
        report.update(scenario='expand', run_id='test', commit='<script>alert(1)</script>',
                      fixture_sha256='digest', limitations=['Synthetic fixture only'],
                      verdict='GO_WITHIN_SCOPE')
        with tempfile.TemporaryDirectory() as directory:
            write_reports(report, directory)
            output = (Path(directory) / 'expand.html').read_text()
            self.assertNotIn('<script>', output)
            self.assertIn('&lt;script&gt;', output)


if __name__ == '__main__':
    unittest.main()
