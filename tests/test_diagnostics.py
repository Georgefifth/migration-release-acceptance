import copy
import json
import unittest

from acceptance.diagnostics import summary_lines, troubleshooting
from acceptance.runner import CHECK_IDS, verdict
from test_gate import complete


class DiagnosticsTests(unittest.TestCase):
    def test_baseline_failure_is_not_described_as_candidate_incompatibility(self):
        report = complete()
        report['checks'][CHECK_IDS.index('baseline_read')].update(status='FAIL', failure_kind='compatibility', sqlstate='42703')
        report['verdict'] = verdict(report)
        before = copy.deepcopy(report)
        self.assertEqual(troubleshooting(report)[0]['code'], 'baseline_setup')
        self.assertEqual(report, before)
        self.assertEqual(report['verdict'], 'INCONCLUSIVE')

    def test_cleanup_failure_does_not_erase_the_observed_compatibility_failure(self):
        report = complete()
        report['checks'][CHECK_IDS.index('old_read')].update(status='FAIL', failure_kind='compatibility', sqlstate='42703')
        report.update(cleanup_ok=False, cleanup_evidence={'schema_state': 'unconfirmed', 'schema': 'acceptance_' + 'a' * 32})
        report['verdict'] = verdict(report)
        issues = troubleshooting(report)
        self.assertEqual([i['code'] for i in issues], ['compatibility', 'cleanup_unconfirmed'])
        self.assertIn('acceptance_' + 'a' * 32, issues[-1]['detail'])
        self.assertEqual(report['verdict'], 'INCONCLUSIVE')

    def test_completed_checks_with_failed_cleanup_do_not_claim_execution_incomplete(self):
        report = complete()
        report.update(cleanup_ok=False, verdict='INCONCLUSIVE')
        self.assertEqual([i['code'] for i in troubleshooting(report)], ['cleanup_unconfirmed'])

    def test_unrecognized_context_and_private_messages_do_not_enter_guidance(self):
        report = dict(verdict='INCONCLUSIVE', completed=False, cleanup_ok=False, checks=[],
                      error={'kind': 'RuntimeError', 'message': 'private-value'},
                      error_context={'phase': 'private-value'},
                      cleanup_evidence={'schema_state': 'unconfirmed', 'schema': 'private-value'})
        self.assertNotIn('private-value', json.dumps(troubleshooting(report)))
        self.assertNotIn('private-value', '\n'.join(summary_lines(report)))

    def test_new_app_startup_reports_the_failed_phase_without_overriding_verdict(self):
        report = dict(verdict='INCONCLUSIVE', completed=False, cleanup_ok=True, checks=[],
                      error_context={'phase': 'application_checks', 'check_id': 'new_application_started'})
        self.assertEqual(troubleshooting(report)[0]['title'], 'The new application did not become ready.')
        self.assertTrue(summary_lines(report)[0].endswith('INCONCLUSIVE'))
