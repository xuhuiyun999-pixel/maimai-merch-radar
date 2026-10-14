import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from maimai_radar.config import load_token


class ConfigTests(unittest.TestCase):
    def test_missing_token_explains_local_configuration(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'configure'):
                load_token(Path(folder))

    def test_reads_private_file_without_cwd_dependency(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            root = Path(folder)
            (root / '.env').write_text('MCD_MCP_TOKEN=synthetic-key\n', encoding='utf-8')
            self.assertEqual(load_token(root), 'synthetic-key')

    def test_environment_overrides_private_file(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'MCD_MCP_TOKEN': 'env-key'}, clear=True):
            root = Path(folder)
            (root / '.env').write_text('MCD_MCP_TOKEN=file-key\n', encoding='utf-8')
            self.assertEqual(load_token(root), 'env-key')
