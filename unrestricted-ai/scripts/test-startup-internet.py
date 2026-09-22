import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('startup_internet', Path(__file__).with_name('check-startup-internet.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InternetDiagnosticsTests(unittest.TestCase):
    def test_success(self):
        with patch.object(module.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as run:
            report = module.check()
        self.assertTrue(report['allProbesPassed'])
        self.assertEqual(run.call_count, 2)
        self.assertTrue(all(c.kwargs['timeout'] == 8 for c in run.call_args_list))

    def test_one_source_unavailable(self):
        def response(args, **kwargs):
            return subprocess.CompletedProcess(args, int(args[-1] == module.URLS[0]))
        with patch.object(module.subprocess, 'run', side_effect=response):
            report = module.check()
        self.assertTrue(report['internetReachable'])
        self.assertFalse(report['allProbesPassed'])

    def test_failed_dns_or_https(self):
        with patch.object(module.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)):
            self.assertFalse(module.check()['internetReachable'])

    def test_dns_timeout_is_bounded(self):
        with patch.object(module.subprocess, 'run', side_effect=subprocess.TimeoutExpired('probe', 8)):
            report = module.check()
        self.assertFalse(report['internetReachable'])
        self.assertTrue(all('8 seconds' in p['error'] for p in report['probes']))


if __name__ == '__main__':
    unittest.main()
