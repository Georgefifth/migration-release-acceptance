"""Verify the HTTP error boundary cannot leak server text or invent SQLSTATE."""
import io
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError
from acceptance.http_client import Application, ApplicationError


class HttpEvidenceTests(unittest.TestCase):
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
