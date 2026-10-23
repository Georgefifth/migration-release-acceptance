import unittest
from integrations.fastapi_case import isolated_environment


class UpstreamEnvironmentTests(unittest.TestCase):
    def test_child_does_not_inherit_ci_or_developer_credentials(self):
        child = isolated_environment({'PATH': '/usr/bin', 'DATABASE_URL': 'synthetic-test-dsn',
                                      'ACCEPTANCE_SCHEMA': 'acceptance_test',
                                      'ACCEPTANCE_DISPOSABLE_DB': 'yes',
                                      'CI_JOB_TOKEN': 'sensitive', 'AWS_SECRET_ACCESS_KEY': 'sensitive',
                                      'HOME': '/private'})
        self.assertNotIn('CI_JOB_TOKEN', child)
        self.assertNotIn('AWS_SECRET_ACCESS_KEY', child)
        self.assertNotIn('HOME', child)
        self.assertEqual(child['DATABASE_URL'], 'synthetic-test-dsn')
        self.assertEqual(child['ACCEPTANCE_DISPOSABLE_DB'], 'yes')


if __name__ == '__main__':
    unittest.main()
