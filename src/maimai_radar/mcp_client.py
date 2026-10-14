import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any

from .models import QueryResult

SERVER_URL = 'https://mcp.mcd.cn'
READONLY_TOOLS = frozenset({'mall-points-products', 'mall-product-detail', 'campaign-calendar'})


def now() -> str:
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')


def redact(value: Any, token: str) -> Any:
    if isinstance(value, str):
        return value.replace(token, '[已隐藏]') if token else value
    if isinstance(value, dict):
        return {str(k): redact(v, token) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, token) for v in value]
    return value


def decode_result(result) -> Any:
    structured = getattr(result, 'structuredContent', None)
    if structured is not None:
        return structured
    texts = [block.text for block in result.content if getattr(block, 'type', '') == 'text']
    text = '\n'.join(texts)
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return {'text': text}


def business_failed(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get('success') is False:
        return True
    code = payload.get('code')
    return code is not None and str(code) not in {'0', '200', '0000', 'SUCCESS'}


async def call_readonly(session, name: str, arguments: dict, token: str) -> QueryResult:
    if name not in READONLY_TOOLS:
        raise ValueError('该工具不在本项目的只读查询范围内。')
    timestamp = now()
    try:
        result = await asyncio.wait_for(session.call_tool(name, arguments), timeout=45)
        payload = redact(decode_result(result), token)
        if getattr(result, 'isError', False) or business_failed(payload):
            if name == 'mall-product-detail' and isinstance(payload, dict) and str(payload.get('code')) == '610403':
                return QueryResult(name, 'failed', queried_at=timestamp, message='商品已下架，详情接口未返回商品资料。请在官方渠道查看当前可用商品。')
            return QueryResult(name, 'failed', queried_at=timestamp, message='服务返回查询失败；请检查凭据或稍后手动重试。')
        return QueryResult(name, 'ok', payload, timestamp)
    except Exception:
        return QueryResult(name, 'failed', queried_at=timestamp, message='查询未成功；请检查连接或凭据后手动重试。')


@asynccontextmanager
async def connect(token: str):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    # Library HTTP diagnostics may contain service data; keep them out of user output.
    for logger in ('httpx', 'httpcore', 'mcp'):
        logging.getLogger(logger).setLevel(logging.CRITICAL)
    async with streamablehttp_client(
        SERVER_URL, headers={'Authorization': f'Bearer {token}'},
        timeout=timedelta(seconds=25), sse_read_timeout=timedelta(seconds=50),
        terminate_on_close=False,
    ) as (read, write, _):
        async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=50)) as session:
            await session.initialize()
            yield session


async def list_tools(session) -> dict[str, dict]:
    tools = {}
    cursor = None
    seen = set()
    for _ in range(20):
        page = await session.list_tools(cursor=cursor)
        for tool in page.tools:
            if tool.name in READONLY_TOOLS:
                tools[tool.name] = tool.model_dump(mode='json', exclude_none=True)
        cursor = page.nextCursor
        if not cursor:
            return tools
        if cursor in seen:
            raise ValueError('工具列表分页不完整，无法安全确认可用查询。')
        seen.add(cursor)
    raise ValueError('工具列表分页过多，请稍后手动重试。')


async def discover_tools(token: str) -> dict[str, dict]:
    async with asyncio.timeout(60):
        async with connect(token) as session:
            return redact(await list_tools(session), token)


async def collect_from_session(session, requests: dict[str, dict], token: str) -> list[QueryResult]:
    from jsonschema import validate, ValidationError, SchemaError

    if not set(requests).issubset(READONLY_TOOLS):
        raise ValueError('请求包含不允许的业务工具。')
    available = await list_tools(session)
    results = []
    for name, arguments in requests.items():
        if name not in available:
            results.append(QueryResult(name, 'unsupported', queried_at=now(), message='服务未提供此查询工具。'))
            continue
        try:
            validate(arguments, available[name]['inputSchema'])
        except ValidationError:
            results.append(QueryResult(name, 'needs_input', queried_at=now(), message='查询参数缺失或格式不符合服务要求，请查看工具输入结构。'))
            continue
        except SchemaError:
            results.append(QueryResult(name, 'unsupported', queried_at=now(), message='服务输入结构无法验证，已停止此项查询。'))
            continue
        results.append(await call_readonly(session, name, arguments, token))
    return results


async def collect(token: str, requests: dict[str, dict]) -> list[QueryResult]:
    if not set(requests).issubset(READONLY_TOOLS):
        raise ValueError('请求包含不允许的业务工具。')
    try:
        async with asyncio.timeout(150):
            async with connect(token) as session:
                return await collect_from_session(session, requests, token)
    except Exception:
        return [QueryResult(name, 'failed', queried_at=now(), message='连接或工具发现未成功，请检查网络和凭据。') for name in requests]
