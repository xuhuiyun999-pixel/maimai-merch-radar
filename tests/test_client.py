import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from maimai_radar.mcp_client import call_readonly


class ClientTests(unittest.IsolatedAsyncioTestCase):
    async def test_write_tool_is_rejected_before_network(self):
        session = SimpleNamespace(call_tool=AsyncMock())
        with self.assertRaises(ValueError):
            await call_readonly(session, 'mall-create-order', {}, 'test-secret')
        session.call_tool.assert_not_called()

    async def test_business_error_is_failed(self):
        session = SimpleNamespace(call_tool=AsyncMock(return_value=SimpleNamespace(
            isError=True, structuredContent=None,
            content=[SimpleNamespace(type='text', text='query failed')],
        )))
        result = await call_readonly(session, 'campaign-calendar', {}, 'test-secret')
        self.assertEqual(result.status, 'failed')

    async def test_json_business_error_is_failed(self):
        session = SimpleNamespace(call_tool=AsyncMock(return_value=SimpleNamespace(
            isError=False, structuredContent=None,
            content=[SimpleNamespace(type='text', text='{"success":false,"message":"denied"}')],
        )))
        result = await call_readonly(session, 'campaign-calendar', {}, 'test-secret')
        self.assertEqual(result.status, 'failed')

    async def test_error_does_not_expose_token(self):
        session = SimpleNamespace(call_tool=AsyncMock(side_effect=RuntimeError('test-secret')))
        result = await call_readonly(session, 'campaign-calendar', {}, 'test-secret')
        self.assertNotIn('test-secret', repr(result))
        self.assertEqual(result.status, 'failed')

    async def test_success_redacts_token_recursively(self):
        session = SimpleNamespace(call_tool=AsyncMock(return_value=SimpleNamespace(
            isError=False, structuredContent={'data': {'message': 'test-secret'}}, content=[],
        )))
        result = await call_readonly(session, 'campaign-calendar', {}, 'test-secret')
        self.assertNotIn('test-secret', repr(result))
        self.assertEqual(result.status, 'ok')

    async def test_delisted_detail_has_explicit_safe_reason(self):
        session = SimpleNamespace(call_tool=AsyncMock(return_value=SimpleNamespace(
            isError=False, structuredContent={'success': False, 'code': 610403, 'message': '商品已下架 synthetic-secret'}, content=[],
        )))
        result = await call_readonly(session, 'mall-product-detail', {'spuId': 1}, 'synthetic-secret')
        self.assertEqual(result.status, 'failed')
        self.assertIn('商品已下架', result.message)
        self.assertNotIn('synthetic-secret', repr(result))
        self.assertIsNone(result.payload)
