from .models import Card, QueryResult


def demo_data():
    timestamp = '2026-10-14T12:00:00+08:00'
    results = [QueryResult('mall-points-products', 'ok', queried_at=timestamp, message='虚构样例，不代表真实商品。')]
    cards = [Card('虚构样例 · 小汉堡挂件', '周边商品', '800', '0', '虚构日期，仅用于排版预览',
                  '此商品与兑换条件均为虚构，不可据此参与活动。', source_tool='mall-points-products', phase='虚构样例')]
    return results, cards
