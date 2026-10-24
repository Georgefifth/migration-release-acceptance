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
    def dependency_report(self):
        report = complete()
        report['checks'][CHECK_IDS.index('new_write')].update(
            status='FAIL', failure_kind='compatibility', sqlstate='23505', write_acknowledged=False)
        report['checks'][CHECK_IDS.index('rollback_new_data')].update(
            status='SKIP', failure_kind='dependency', depends_on='new_write',
            reason_code='create_not_acknowledged')
        return report

    def test_failed_create_preserves_block_with_a_valid_dependent_skip(self):
        self.assertEqual(verdict(self.dependency_report()), 'BLOCK')

    def test_dependency_skip_cannot_hide_unknown_request_or_cleanup_failure(self):
        for mode in ('parent_unknown', 'other_unknown', 'cleanup'):
            report = self.dependency_report()
            if mode == 'parent_unknown':
                report['checks'][CHECK_IDS.index('new_write')]['failure_kind'] = 'infrastructure_or_unknown'
            elif mode == 'other_unknown':
                report['checks'][CHECK_IDS.index('old_read')].update(status='FAIL', failure_kind='infrastructure_or_unknown')
            else:
                report['cleanup_ok'] = False
            with self.subTest(mode=mode):
                self.assertEqual(verdict(report), 'INCONCLUSIVE')

    def test_forged_or_unrelated_skips_never_allow_go_or_block(self):
        for mode in ('parent_pass', 'acknowledged', 'missing_ack', 'wrong_dependency', 'wrong_reason', 'wrong_kind', 'wrong_check'):
            report = self.dependency_report()
            parent = report['checks'][CHECK_IDS.index('new_write')]
            skip = report['checks'][CHECK_IDS.index('rollback_new_data')]
            if mode == 'parent_pass': parent['status'] = 'PASS'
            elif mode == 'acknowledged': parent['write_acknowledged'] = True
            elif mode == 'missing_ack': parent.pop('write_acknowledged')
            elif mode == 'wrong_dependency': skip['depends_on'] = 'old_write'
            elif mode == 'wrong_reason': skip['reason_code'] = 'anything'
            elif mode == 'wrong_kind': skip['failure_kind'] = 'compatibility'
            elif mode == 'wrong_check':
                report['checks'][-2], report['checks'][-1] = skip, report['checks'][-2]
                skip['id'], report['checks'][-1]['id'] = 'rollback_read', 'rollback_new_data'
            with self.subTest(mode=mode): self.assertEqual(verdict(report), 'INCONCLUSIVE')

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
        for name in ['applications_started', 'new_application_started', 'baseline_read',
                     'baseline_write', 'migration', 'rollback_restart']:
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
                      workload='<svg onload=alert(1)>', provenance={'repository': '<script>upstream</script>'},
                      verdict='GO_WITHIN_SCOPE')
        with tempfile.TemporaryDirectory() as directory:
            write_reports(report, directory)
            output = (Path(directory) / 'expand.html').read_text()
            self.assertNotIn('<script>', output)
            self.assertIn('&lt;script&gt;', output)
            self.assertNotIn('<svg', output)
            self.assertIn('&lt;svg', output)
            self.assertIn('&lt;script&gt;upstream', output)


if __name__ == '__main__':
    unittest.main()
