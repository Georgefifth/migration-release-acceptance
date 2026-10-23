"""Resource ownership and interruption boundaries of the first-trial entry point."""
import contextlib
import io
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from acceptance import trial


class TrialTests(unittest.TestCase):
    def test_missing_docker_never_starts_a_command(self):
        output = io.StringIO()
        with patch.object(trial.shutil, 'which', return_value=None), patch.object(trial, 'command') as command, contextlib.redirect_stderr(output):
            self.assertEqual(trial.main([]), 2)
        command.assert_not_called()
        self.assertIn('Docker is missing', output.getvalue())

    def test_cleanup_requires_matching_ownership_and_removes_volumes(self):
        with patch.object(trial, 'command', return_value=(0, 'another-trial')) as command:
            self.assertFalse(trial.remove_owned_container('owned-name', 'this-trial'))
            self.assertEqual(command.call_count, 1)
        with patch.object(trial, 'command', side_effect=[(0, 'this-trial'), (0, 'owned-name')]) as command:
            self.assertTrue(trial.remove_owned_container('owned-name', 'this-trial'))
            self.assertEqual(command.call_args.args[0], ['docker', 'rm', '--force', '--volumes', 'owned-name'])

    def test_check_does_not_create_resources_or_expose_existing_dsn(self):
        output = io.StringIO()
        with patch.object(trial.shutil, 'which', return_value='/usr/bin/docker'), patch.object(trial, 'command', return_value=(0, '')) as command, patch.dict(os.environ, DATABASE_URL='postgresql://private-secret'), contextlib.redirect_stdout(output):
            self.assertEqual(trial.main(['--check']), 0)
        self.assertEqual(command.call_count, 2)
        self.assertNotIn('private-secret', output.getvalue())

    @unittest.skipUnless(os.name == 'posix', 'Process group cleanup uses POSIX signals')
    def test_timed_out_worker_stops_its_descendant(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / 'descendant-stopped'
            ready = Path(temporary) / 'ready'
            child = ('import signal,time,pathlib; '
                     f'signal.signal(signal.SIGTERM, lambda *_: (pathlib.Path({str(marker)!r}).touch(), exit(0))); '
                     f'pathlib.Path({str(ready)!r}).touch(); time.sleep(30)')
            parent = ('import subprocess,sys,time; '
                      f'subprocess.Popen([sys.executable,"-c",{child!r}]); time.sleep(30)')
            with self.assertRaises(subprocess.TimeoutExpired):
                trial.command([sys.executable, '-c', parent], timeout=2)
            self.assertTrue(ready.exists(), 'Descendant must be running before timeout')
            for _ in range(20):
                if marker.exists():
                    break
                time.sleep(.05)
            self.assertTrue(marker.exists(), 'Descendant must receive cleanup signal')
