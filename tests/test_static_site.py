"""A public sample must preserve evidence and have no broken local actions."""
import contextlib
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

from tools.build_site import build, ROOT


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = set()
        self.links = []
        self.scripts = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.targets.add(attrs['id'])
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
        if tag == 'script':
            self.scripts += 1


class StaticSiteTests(unittest.TestCase):
    def test_build_keeps_reports_and_all_local_links_work_without_scripts(self):
        with tempfile.TemporaryDirectory() as temporary, contextlib.redirect_stdout(io.StringIO()):
            folder = Path(temporary)
            identity = build(folder)
            self.assertTrue(identity['static_only'])
            for sample in identity['samples']:
                name = sample['candidate'] + '.json'
                self.assertEqual(json.loads((folder / 'reports' / name).read_text()),
                                 json.loads((ROOT / 'demo/evidence' / name).read_text()))
            for page in folder.rglob('*.html'):
                parsed = Links()
                parsed.feed(page.read_text())
                self.assertEqual(parsed.scripts, 0)
                for href in parsed.links:
                    link = urlsplit(href)
                    if link.scheme or link.netloc:
                        self.assertIn(link.scheme, {'http', 'https'})
                        self.assertFalse(link.username)
                        continue
                    target = (page.parent / unquote(link.path)).resolve() if link.path else page
                    self.assertTrue(target.is_relative_to(folder.resolve()))
                    self.assertTrue(target.is_file(), href)
                    if link.fragment:
                        destination = Links()
                        destination.feed(target.read_text())
                        self.assertIn(unquote(link.fragment), destination.targets)

    def test_mismatched_sample_does_not_publish_partial_pages(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch('tools.build_site.load_report', return_value={
                    'commit': 'unreviewed', 'run_id': 'not-the-recorded-run'}):
                with self.assertRaisesRegex(ValueError, 'identity or scope'):
                    build(temporary)
            self.assertEqual(list(Path(temporary).rglob('*.html')), [])


if __name__ == '__main__':
    unittest.main()
