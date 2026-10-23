import copy
import json
import tempfile
import unittest
from pathlib import Path
from acceptance.report import write_reports
from acceptance.report_ui import comparison_gap, comparison_report, introduction, link
from test_gate import complete


def run_report(scenario='expand'):
    report = complete()
    report.update(scenario=scenario, verdict='GO_WITHIN_SCOPE', commit='verified-sha',
                  run_id=scenario+'-run', fixture_sha256='digest', transport='HTTP',
                  workload='items', application_factory='project:Adapter',
                  limitations=['Synthetic data only'], provenance={'commit': 'upstream-sha'})
    return report


class ReportViewTests(unittest.TestCase):
    def test_named_project_candidate_links_only_its_own_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            write_reports(run_report('item-title-storage'), directory)
            page = (Path(directory) / 'item-title-storage.html').read_text()
            self.assertIn('href="item-title-storage.json"', page)
            self.assertNotIn('href="comparison.html"', page)

    def test_different_or_incomplete_runs_never_get_an_operation_comparison(self):
        left = run_report('breaking')
        for field, value in [('commit', 'other-sha'), ('workload', 'other'),
                             ('provenance', {'commit': 'other'}), ('application_factory', None), ('cleanup_ok', False)]:
            with self.subTest(field=field):
                right = run_report()
                right[field] = value
                self.assertIsNotNone(comparison_gap(left, right))
                self.assertNotIn('class="comparison"', comparison_report(left, right))
        right = run_report()
        right['checks'][0]['operation'] = 'Different operation'
        self.assertIsNotNone(comparison_gap(left, right))
        right = run_report()
        right['checks'].append(copy.deepcopy(right['checks'][0]))
        self.assertIsNotNone(comparison_gap(left, right))

    def test_matching_runs_keep_actual_verdicts_and_generate_links(self):
        left, right = run_report('breaking'), run_report()
        left.update(verdict='BLOCK')
        left['checks'][5].update(status='FAIL', sqlstate='42703')
        self.assertIsNone(comparison_gap(left, right))
        output = comparison_report(left, right)
        self.assertIn('BLOCK', output)
        self.assertIn('GO_WITHIN_SCOPE', output)
        self.assertIn('42703', output)
        self.assertIn('class="comparison"', output)
        with tempfile.TemporaryDirectory() as directory:
            write_reports(left, directory)
            self.assertIn('A second run is needed', (Path(directory)/'comparison.html').read_text())
            self.assertNotIn('href="expand.html"', (Path(directory)/'comparison.html').read_text())
            write_reports(right, directory)
            self.assertIn('class="comparison"', (Path(directory)/'comparison.html').read_text())

    def test_malformed_counterpart_does_not_break_a_valid_report(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory)/'breaking.json').write_text(json.dumps(['not a report']))
            write_reports(run_report(), directory)
            self.assertTrue((Path(directory)/'expand.html').exists())
            self.assertIn('A second run is needed', (Path(directory)/'comparison.html').read_text())

    def test_report_output_cannot_escape_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                write_reports(run_report('../outside'), directory)

    def test_unsafe_link_schemes_are_not_rendered(self):
        for url in ['javascript:alert(1)', 'data:text/html,bad', 'https://user:password@example.com']:
            self.assertNotIn('href=', link(url, 'pipeline'))
        self.assertIn('href=', link('https://gitlab.com/project/pipeline', 'pipeline'))

    def test_incomplete_run_does_not_receive_success_headline(self):
        report = run_report()
        report['completed'] = False
        self.assertIn('cannot establish', introduction(report))


if __name__ == '__main__':
    unittest.main()
