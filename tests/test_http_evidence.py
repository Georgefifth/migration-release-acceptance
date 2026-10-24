"""Verify the HTTP error boundary cannot leak server text or invent SQLSTATE."""
import io
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError
from acceptance.http_client import Application, ApplicationError


class HttpEvidenceTests(unittest.TestCase):
    def test_missing_record_requires_exact_protocol_marker_and_http_status(self):
        for status,body,reason in [
            (404,b'{"error":"record_missing","detail":"private"}','record_missing'),
            (404,b'{"error":"unknown_route"}',None),
            (500,b'{"error":"record_missing"}',None),
            (403,b'{"error":"record_missing"}',None),
            (404,b'{"detail":"record_missing"}',None),
            (404,b'[]',None),
        ]:
            with self.subTest(status=status,body=body):
                app=Application('v1','unused','unused');app.url='http://127.0.0.1:1';app.opener=Mock()
                app.opener.open.side_effect=HTTPError(app.url,status,'private',{},io.BytesIO(body))
                with self.assertRaises(ApplicationError) as caught:app.read(None,1)
                self.assertEqual(caught.exception.reason,reason)
                self.assertEqual(str(caught.exception),'')

    def test_direct_adapter_errors_validate_state_and_erase_untrusted_text(self):
        for state,expected in [('22P02','22P02'),('秘密秘密秘',None),('2350a',None),
                               ('postgresql://private',None),(None,None)]:
            error=ApplicationError(state,reason='private error text')
            self.assertEqual(error.sqlstate,expected)
            self.assertIsNone(error.reason)
            self.assertEqual(str(error),'')

    def test_only_validated_sqlstate_crosses_http_boundary(self):
        for body, expected in [
            (b'{"error":"database","sqlstate":"42703","detail":"private row"}', '42703'),
            (b'{"sqlstate":"postgresql://secret"}', None),
            (b'{"error":"application"}', None),
            (b'<html>private server error</html>', None),
        ]:
            with self.subTest(body=body):
                app = Application('v1', 'unused', 'unused')
                app.url = 'http://127.0.0.1:1'
                app.opener = Mock()
                app.opener.open.side_effect = HTTPError(
                    app.url, 500, 'private error', {}, io.BytesIO(body))
                with self.assertRaises(ApplicationError) as caught:
                    app.read(None, 1)
                self.assertEqual(caught.exception.sqlstate, expected)
                self.assertNotIn('private', str(caught.exception))
                self.assertNotIn('secret', str(caught.exception))


if __name__ == '__main__':
    unittest.main()
