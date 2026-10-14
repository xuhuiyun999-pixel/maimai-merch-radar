import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from maimai_radar.cli import main
from maimai_radar.models import QueryResult


class CliTests(unittest.TestCase):
    def test_discovery_exception_never_prints_external_value_error(self):
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as folder, patch('maimai_radar.cli.project_root', return_value=Path(folder)), patch('maimai_radar.cli.load_token', return_value='synthetic-secret'), patch('maimai_radar.cli.discover_tools', new=AsyncMock(side_effect=ValueError('remote includes synthetic-secret'))), patch('sys.argv', ['radar', 'discover']), contextlib.redirect_stdout(output):
            self.assertEqual(main(), 1)
        self.assertNotIn('synthetic-secret', output.getvalue())

    def test_missing_credentials_replaces_stale_success_report(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            root = Path(folder)
            (root / 'output').mkdir()
            (root / 'output/radar.json').write_text('{"cards":[{"title":"STALE"}]}', encoding='utf-8')
            with patch('maimai_radar.cli.project_root', return_value=root), patch('sys.argv', ['radar', 'query']), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 1)
            result = json.loads((root / 'output/radar.json').read_text(encoding='utf-8'))
            self.assertEqual(result['cards'], [])
            self.assertTrue(all(q['status'] == 'failed' for q in result['queries']))

    def test_changed_product_field_type_retains_successful_calendar(self):
        products = QueryResult('mall-points-products', 'ok', {'data': [{'spuName': '虚构礼盒', 'catName': ['玩具']}]})
        calendar = QueryResult('campaign-calendar', 'ok', {'data': {'dailyList': [{'date': '2026-10-14', 'events': [{'activityTitle': '虚构周边活动'}]}]}})
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch('maimai_radar.cli.project_root', return_value=root), patch('maimai_radar.cli.load_token', return_value='synthetic-secret'), patch('maimai_radar.cli.collect', new=AsyncMock(return_value=[products, calendar])), patch('sys.argv', ['radar', 'query']), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 0)
            result = json.loads((root / 'output/radar.json').read_text(encoding='utf-8'))
            self.assertIn('虚构周边活动', [c['title'] for c in result['cards']])
            self.assertEqual(result['cards'][0]['kind'], '类型待确认')

    def test_detail_failure_does_not_overwrite_overview(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'output').mkdir()
            overview = root / 'output/radar.json'
            overview.write_text('{"cards":[{"title":"OVERVIEW"}]}', encoding='utf-8')
            (root / 'output/radar.html').write_text('OVERVIEW HTML', encoding='utf-8')
            arguments = root / 'arguments.json'
            arguments.write_text('{"spuId":1}', encoding='utf-8')
            results = [QueryResult('mall-product-detail', 'failed', message='商品已下架')]
            with patch('maimai_radar.cli.project_root', return_value=root), patch('maimai_radar.cli.load_token', return_value='synthetic-secret'), patch('maimai_radar.cli.collect', new=AsyncMock(return_value=results)), patch('sys.argv', ['radar', 'query', '--tool', 'mall-product-detail', '--arguments-file', str(arguments)]), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 1)
            self.assertEqual(overview.read_text(encoding='utf-8'), '{"cards":[{"title":"OVERVIEW"}]}')
            self.assertEqual((root / 'output/radar.html').read_text(encoding='utf-8'), 'OVERVIEW HTML')
            detail = json.loads((root / 'output/details/radar.json').read_text(encoding='utf-8'))
            self.assertEqual(detail['queries'][0]['status'], 'failed')

    def test_detail_configuration_failure_does_not_overwrite_overview(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            root = Path(folder)
            (root / 'output').mkdir()
            overview = root / 'output/radar.json'
            overview.write_text('OVERVIEW', encoding='utf-8')
            with patch('maimai_radar.cli.project_root', return_value=root), patch('sys.argv', ['radar', 'query', '--tool', 'mall-product-detail']), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(), 1)
            self.assertEqual(overview.read_text(encoding='utf-8'), 'OVERVIEW')
            self.assertTrue((root / 'output/details/radar.html').is_file())
