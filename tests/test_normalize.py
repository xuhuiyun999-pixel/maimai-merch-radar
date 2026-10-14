import unittest

from maimai_radar.models import QueryResult
from maimai_radar.normalize import normalize


class NormalizeTests(unittest.TestCase):
    def product(self, **fields):
        item = {'spuName': '虚构测试礼盒', 'spuId': 1, **fields}
        return QueryResult('mall-points-products', 'ok', {'success': True, 'data': [item]}, '2026-10-14T12:00:00+08:00')

    def test_missing_fields_remain_unknown(self):
        card = normalize(self.product())[0]
        self.assertIsNone(card.points)
        self.assertIsNone(card.dates)

    def test_unknown_shape_is_not_empty(self):
        result = QueryResult('mall-points-products', 'ok', {'unexpected': []})
        self.assertEqual(normalize(result), [])
        self.assertEqual(result.status, 'unsupported')

    def test_truncated_list_has_partial_coverage(self):
        result = self.product(catName='玩具')
        result.payload['hasMore'] = True
        normalize(result)
        self.assertEqual(result.coverage, 'partial')

    def test_ambiguous_item_kind_is_unknown(self):
        self.assertEqual(normalize(self.product())[0].kind, '类型待确认')

    def test_past_display_period_is_not_current_stock(self):
        card = normalize(self.product(catName='玩具', downTime='2026-08-14 23:59:59'))[0]
        self.assertEqual(card.phase, '已过接口展示期限')

    def test_zero_values_are_preserved(self):
        card = normalize(self.product(point='0', price='0'))[0]
        self.assertEqual(card.points, '0')
        self.assertEqual(card.cash, '0')

    def test_calendar_date_is_not_claimed_as_expiry(self):
        result = QueryResult('campaign-calendar', 'ok', {'data': {'dailyList': [{
            'date': '2026-10-13', 'events': [{'activityCode': 'synthetic', 'articleDto': {
                'title': '虚构联名活动', 'content': '活动期限另见说明',
                'appJumpUrl': 'mcdapp://private-target',
            }}],
        }]}}, '2026-10-14T12:00:00+08:00')
        card = normalize(result)[0]
        self.assertIn('日历展示', card.dates)
        self.assertIsNone(card.source_url)
        self.assertEqual(card.kind, '周边活动线索')
        self.assertEqual(result.coverage, 'unknown')

    def test_event_without_article_uses_activity_fields(self):
        result = QueryResult('campaign-calendar', 'ok', {'data': {'dailyList': [{
            'date': '2026-10-15', 'events': [{'activityTitle': '虚构玩具活动', 'activitySubTitle': '原始说明'}],
        }]}}, '2026-10-14T12:00:00+08:00')
        self.assertEqual(normalize(result)[0].title, '虚构玩具活动')
