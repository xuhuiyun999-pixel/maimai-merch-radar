import unittest

from maimai_radar.models import Card, QueryResult
from maimai_radar.report import render_report


class ReportTests(unittest.TestCase):
    def test_script_payload_is_escaped(self):
        card = Card('<script>alert(1)</script>', '周边商品', description='<img src=x onerror=alert(1)>')
        html = render_report([], [card])
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertNotIn('<img src=x', html)
        self.assertIn('&lt;script&gt;', html)

    def test_non_http_source_is_not_linked(self):
        html = render_report([], [Card('虚构测试', '周边商品', source_url='javascript:alert(1)')])
        self.assertNotIn('href="javascript:', html)

    def test_partial_failure_stays_visible(self):
        results = [QueryResult('campaign-calendar', 'failed', message='活动查询失败'), QueryResult('mall-points-products', 'ok')]
        html = render_report(results, [Card('虚构礼盒', '周边商品')])
        self.assertIn('活动查询失败', html)
        self.assertIn('虚构礼盒', html)
        self.assertIn('部分查询未完成', html)

    def test_demo_is_clearly_labelled(self):
        self.assertIn('虚构样例', render_report([], [], demo=True))

    def test_unknown_fields_and_past_period_are_visible(self):
        html = render_report([], [Card('虚构礼盒', '周边商品', phase='已过接口展示期限')])
        self.assertIn('接口未提供', html)
        self.assertIn('已过接口展示期限', html)

    def test_no_remote_assets_are_loaded_automatically(self):
        html = render_report([], [Card('虚构礼盒', '周边商品')])
        self.assertNotIn('<img', html)
        self.assertNotIn('<script src=', html)
        self.assertNotIn('@import', html)

    def test_detail_report_does_not_claim_calendar_query_or_merch_filter(self):
        results = [QueryResult('mall-product-detail', 'failed', message='商品已下架')]
        html = render_report(results, [])
        self.assertIn('未能取得商品详情', html)
        self.assertIn('商品已下架', html)
        self.assertNotIn('已使用接口提供的周边类目筛选', html)
        self.assertNotIn('<h2>周边活动线索</h2>', html)
        self.assertNotIn('部分查询未完成', html)

    def test_successful_detail_shows_specs_notes_and_voucher_cost_boundary(self):
        from maimai_radar.normalize import normalize
        result = QueryResult('mall-product-detail', 'ok', {'data': {
            'spuName': '虚构餐券', 'spuId': 1, 'categoryRuleId': '1>4>13',
            'skuList': [{'skuId': 2, 'points': '800', 'price': '0', 'extTradePrice': '9.9'}],
            'note': '<p>须另付9.9元</p>', 'images': ['https://img.mcd.cn/example.png'],
        }})
        cards = normalize(result)
        html = render_report([result], cards)
        self.assertIn('虚构餐券', html)
        self.assertIn('规格与金额', html)
        self.assertIn('须另付9.9元', html)
        self.assertIn('不等于免费获得餐品', html)
        self.assertIn('https://img.mcd.cn/example.png', html)
        self.assertNotIn('<img', html)
