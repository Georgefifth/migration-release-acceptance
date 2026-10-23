"""Adapter construction failures must not leak previously registered resources."""
import os
import sys
import types
import unittest
from unittest.mock import Mock, patch

from acceptance.runner import run


class DatabaseError(Exception):
    pass


class AdapterCleanupTests(unittest.TestCase):
    def test_second_factory_failure_still_cleans_first_adapter(self):
        first = Mock()
        first.stop.return_value = True

        def factory(version, schema, dsn):
            if version == 'v1':
                return first
            raise RuntimeError('sensitive exception detail must not enter reports')

        database = types.SimpleNamespace(Error=DatabaseError, sql=object(), connect=Mock())
        with patch.dict(sys.modules, {'psycopg': database}), patch.dict(
                os.environ, {'ACCEPTANCE_DISPOSABLE_DB': 'yes'}):
            result = run('expand', 'unused', application_factory=factory)
        first.stop.assert_called_once_with()
        first.start.assert_not_called()
        database.connect.assert_not_called()
        self.assertEqual(result['verdict'], 'INCONCLUSIVE')
        self.assertEqual(result['error'], {'kind': 'RuntimeError'})
        self.assertFalse(result['completed'])
        self.assertFalse(result['cleanup_ok'], 'A failing constructor may not have returned all of its resources')
        self.assertEqual(result['cleanup_evidence']['schema_state'], 'not_requested')
        self.assertNotIn('sensitive', str(result))

    def test_invalid_adapter_contract_is_inconclusive_before_database_access(self):
        class InvalidAdapter:
            def __init__(self, *_):
                pass

            def stop(self):
                return True

        database = types.SimpleNamespace(Error=DatabaseError, sql=object(), connect=Mock())
        with patch.dict(sys.modules, {'psycopg': database}), patch.dict(
                os.environ, {'ACCEPTANCE_DISPOSABLE_DB': 'yes'}):
            result = run('expand', 'unused', application_factory=InvalidAdapter)
        database.connect.assert_not_called()
        self.assertEqual(result['verdict'], 'INCONCLUSIVE')
        self.assertEqual(result['error'], {'kind': 'TypeError'})


if __name__ == '__main__':
    unittest.main()
