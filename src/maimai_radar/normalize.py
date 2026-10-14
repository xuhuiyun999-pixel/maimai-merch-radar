import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from .models import Card, QueryResult

MERCH_WORDS = re.compile(r'周边|联名|联动|玩具|徽章|礼盒|棒球帽|钥匙|公仔|丝巾|贴纸|盲盒|挂件')


def safe_url(value) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        url = urlsplit(value)
        return value if url.scheme.lower() in {'http', 'https'} and url.hostname and not url.username and not url.password else None
    except ValueError:
        return None


def scalar(value):
    return value if isinstance(value, (str, int, float)) and not isinstance(value, bool) else None


def display_phase(item: dict, timestamp: str) -> str:
    try:
        current = datetime.fromisoformat(timestamp)
        zone = timezone(timedelta(hours=8))
        if current.tzinfo is None:
            current = current.replace(tzinfo=zone)
        if item.get('downTime') and datetime.fromisoformat(item['downTime']).replace(tzinfo=zone) < current:
            return '已过接口展示期限'
        if item.get('upTime') and datetime.fromisoformat(item['upTime']).replace(tzinfo=zone) > current:
            return '尚未到接口展示期'
        if item.get('upTime') and item.get('downTime'):
            return '接口展示期内 · 库存未核实'
    except (TypeError, ValueError):
        pass
    return '时间未确认'


def normalize(result: QueryResult) -> list[Card]:
    try:
        return _normalize(result)
    except (TypeError, ValueError, KeyError, AttributeError):
        return unsupported(result)


def _normalize(result: QueryResult) -> list[Card]:
    if result.status not in {'ok', 'empty'}:
        return []
    payload = result.payload
    if not isinstance(payload, dict) or 'data' not in payload:
        return unsupported(result)
    data = payload['data']
    result.coverage = 'partial' if payload.get('hasMore') or payload.get('nextCursor') else 'unknown'
    if result.tool == 'mall-points-products':
        if not isinstance(data, list) or any(not isinstance(item, dict) or not isinstance(item.get('spuName'), str) or not item['spuName'] for item in data):
            return unsupported(result)
        cards = []
        for item in data:
            dates = None
            if item.get('upTime') or item.get('downTime'):
                dates = f"接口展示期：{item.get('upTime') or '接口未提供'} 至 {item.get('downTime') or '接口未提供'}"
            cards.append(Card(
                title=str(item['spuName']),
                kind='周边商品' if isinstance(item.get('catName'), str) and item['catName'] in {'玩具', '鞋袜', '周边', '周边产品', '实物商品'} else '类型待确认',
                points=scalar(item.get('point')), cash=scalar(item.get('price')), dates=dates,
                description=str(item.get('selling') or ''), source_tool=result.tool,
                phase=display_phase(item, result.queried_at), item_id=item.get('spuId'),
            ))
    elif result.tool == 'campaign-calendar':
        if not isinstance(data, dict) or not isinstance(data.get('dailyList'), list):
            return unsupported(result)
        cards = []
        indexed = {}
        for day in data['dailyList']:
            if not isinstance(day, dict) or not isinstance(day.get('events'), list):
                return unsupported(result)
            for event in day['events']:
                if not isinstance(event, dict):
                    return unsupported(result)
                article = event.get('articleDto') or {}
                if not isinstance(article, dict):
                    return unsupported(result)
                title = event.get('activityTitle') or article.get('title')
                if not isinstance(title, str) or not title:
                    return unsupported(result)
                description = article.get('content') or event.get('activitySubTitle') or ''
                key = (str(event.get('activityCode') or title), str(description))
                date = str(day.get('date') or '接口未提供')
                if key in indexed:
                    card = indexed[key]
                    existing = card.dates.removeprefix('日历展示：').removesuffix('（非完整活动期限）').split('、')
                    if date not in existing:
                        existing.append(date)
                    card.dates = '日历展示：' + '、'.join(existing) + '（非完整活动期限）'
                    continue
                card = Card(
                    title=str(title), kind='周边活动线索' if MERCH_WORDS.search(str(title) + str(description)) else '其他活动',
                    dates=f'日历展示：{date}（非完整活动期限）', description=str(description),
                    source_url=safe_url(article.get('appJumpUrl')), source_tool=result.tool,
                    phase='活动参与期限请查看原始说明',
                )
                indexed[key] = card
                cards.append(card)
    else:
        return unsupported(result)
    if not cards:
        result.status = 'empty'
        result.message = '本次接口返回为空；不代表其他日期或门店没有商品或活动。'
    elif result.coverage == 'unknown':
        result.message = '接口未提供明确总量或分页结束标记，仅展示本次返回范围。'
    else:
        result.message = '接口提示仍有后续数据，本报告只展示已返回部分。'
    return cards


def unsupported(result: QueryResult) -> list[Card]:
    result.status = 'unsupported'
    result.message = '返回结构尚未验证，不能将其解释为没有商品或活动。'
    result.coverage = 'unknown'
    return []
