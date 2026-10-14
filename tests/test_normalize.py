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

    def detail(self, **overrides):
        data = {'spuName': '虚构餐券', 'spuId': 1, 'categoryRuleId': '1>4>13',
                'skuList': [{'skuId': 2, 'points': '800', 'price': '0', 'extTradePrice': '9.9'}],
                'note': '<p>须另付9.9元<br>有效期见券面</p>', 'selling': '虚构说明',
                'upDate': '2026-06-01 00:00:00', 'downDate': '2026-12-30 23:59:59', **overrides}
        return QueryResult('mall-product-detail', 'ok', {'success': True, 'data': data}, '2026-10-14T12:00:00+08:00')

    def test_successful_detail_preserves_specs_and_payment_terms(self):
        result = self.detail()
        cards = normalize(result)
        self.assertEqual(result.status, 'ok')
        self.assertEqual(len(cards), 1)
        card = cards[0]
        self.assertEqual(card.kind, '餐券详情（非周边）')
        self.assertEqual(card.skus[0].points, '800')
        self.assertEqual(card.skus[0].cash, '0')
        self.assertEqual(card.skus[0].trade_price, '9.9')
        self.assertIn('须另付9.9元\n有效期见券面', card.notes)
        self.assertIn('非券面有效期', card.dates)

    def test_detail_preserves_all_returned_skus(self):
        cards = normalize(self.detail(skuList=[{'skuId': 2, 'points': '0', 'price': '0'}, {'skuId': 3, 'points': '500', 'price': '1'}]))
        self.assertEqual([s.item_id for s in cards[0].skus], [2, 3])
        self.assertEqual(cards[0].skus[0].points, '0')

    def test_unknown_detail_spec_structure_is_not_empty(self):
        result = self.detail(skuList=['unexpected'])
        self.assertEqual(normalize(result), [])
        self.assertEqual(result.status, 'unsupported')

    def test_detail_rich_text_is_plain_and_images_are_safe_links(self):
        card = normalize(self.detail(note='<p>使用须知</p><script>badcode()</script>', detail='<p>详情文字</p><img src="https://img.mcd.cn/example.png"><img src="javascript:alert(1)">', images=['https://img.mcd.cn/example.png']))[0]
        self.assertNotIn('badcode', card.notes)
        self.assertEqual(card.detail_text, '详情文字')
        self.assertEqual(card.image_urls, ['https://img.mcd.cn/example.png'])
