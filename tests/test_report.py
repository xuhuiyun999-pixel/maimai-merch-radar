import unittest
from html.parser import HTMLParser

from maimai_radar.models import Card, QueryResult
from maimai_radar.report import render_report


class ReportStructure(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.details = []
        self.articles = []
        self.notices = []
        self.article = None
        self.in_title = False
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'details':
            self.details.append(attrs)
        elif tag == 'article':
            history = next((d for d in self.details if d.get('id') == 'history'), None)
            self.article = {'title': '', 'history': history is not None, 'collapsed': history is not None and 'open' not in history}
        elif tag == 'h3':
            self.in_title = True
        elif tag == 'div' and 'notice' in attrs.get('class', '').split():
            self.notices.append(attrs)

    def handle_data(self, data):
        if self.in_title and self.article is not None:
            self.article['title'] += data

    def handle_endtag(self, tag):
        if tag == 'details':
            self.details.pop()
        elif tag == 'h3':
            self.in_title = False
        elif tag == 'article':
            self.articles.append(self.article)
            self.article = None


class ReportTests(unittest.TestCase):
    def test_all_history_is_collapsed_and_informational(self):
        html = render_report([QueryResult('mall-points-products', 'ok')], [
            Card('虚构历史礼盒', '周边商品', source_tool='mall-points-products', phase='已过接口展示期限')])
        page = ReportStructure(html)
        self.assertEqual(page.articles, [{'title': '虚构历史礼盒', 'history': True, 'collapsed': True}])
        self.assertEqual(len(page.notices), 1)
        self.assertEqual(page.notices[0].get('role'), 'status')
        self.assertIn('info', page.notices[0]['class'].split())

    def test_history_does_not_hide_current_or_unknown_records(self):
        html = render_report([], [
            Card('虚构历史礼盒', '周边商品', phase='已过接口展示期限'),
            Card('虚构展示期内商品', '周边商品', phase='接口展示期内 · 库存未核实'),
            Card('虚构日期未知商品', '类型待确认', phase='时间未确认'),
            Card('虚构预告商品', '周边商品', phase='尚未到接口展示期'),
        ])
        articles = {a['title']: a for a in ReportStructure(html).articles}
        self.assertEqual(len(articles), 4)
        self.assertTrue(articles['虚构历史礼盒']['collapsed'])
        for title in ('虚构展示期内商品', '虚构日期未知商品', '虚构预告商品'):
            self.assertFalse(articles[title]['history'])

    def test_history_notice_does_not_suppress_actual_failure(self):
        html = render_report([QueryResult('mall-points-products', 'ok'), QueryResult('campaign-calendar', 'failed', message='活动查询失败')], [
            Card('虚构历史礼盒', '周边商品', source_tool='mall-points-products', phase='已过接口展示期限')])
        notices = ReportStructure(html).notices
        self.assertEqual({n.get('role') for n in notices}, {'status', 'alert'})
        self.assertIn('活动查询失败', html)

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
