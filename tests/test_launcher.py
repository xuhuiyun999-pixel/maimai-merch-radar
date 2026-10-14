import os
import subprocess
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(os.name == 'nt', 'Windows 启动器测试')
class LauncherTests(unittest.TestCase):
    def test_check_mode_preserves_failure_exit_code(self):
        launcher = Path(__file__).resolve().parents[1] / '启动雷达.cmd'
        with tempfile.TemporaryDirectory(prefix='radar cwd with spaces ') as folder:
            env = dict(os.environ, PYTHONHOME=str(Path(folder) / 'nonexistent-python-home'))
            result = subprocess.run(['cmd', '/d', '/c', str(launcher), '--check'], cwd=folder, env=env, capture_output=True, timeout=15)
            self.assertNotEqual(result.returncode, 0, '启动器必须保留 Python 失败的退出码')
