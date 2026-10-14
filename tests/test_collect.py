import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from maimai_radar.mcp_client import collect_from_session


class CollectTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_argument_does_not_call_business_tool(self):
        tool = SimpleNamespace(name='mall-product-detail', model_dump=lambda **k: {
            'inputSchema': {'type': 'object', 'required': ['spuId'], 'properties': {'spuId': {'type': 'integer'}}},
        })
        session = SimpleNamespace(
            list_tools=AsyncMock(return_value=SimpleNamespace(tools=[tool], nextCursor=None)),
            call_tool=AsyncMock(),
        )
        result = await collect_from_session(session, {'mall-product-detail': {}}, 'synthetic-secret')
        self.assertEqual(result[0].status, 'needs_input')
        session.call_tool.assert_not_called()

    async def test_missing_tool_does_not_become_empty(self):
        session = SimpleNamespace(list_tools=AsyncMock(return_value=SimpleNamespace(tools=[], nextCursor=None)))
        result = await collect_from_session(session, {'campaign-calendar': {}}, 'synthetic-secret')
        self.assertEqual(result[0].status, 'unsupported')
