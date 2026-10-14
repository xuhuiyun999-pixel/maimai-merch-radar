from html import escape
from pathlib import Path

from .models import Card, QueryResult
from .normalize import safe_url

CSS = '''
:root{--ink:#292520;--muted:#68635c;--red:#c4212c;--yellow:#ffcc32;--line:#dedbd5;--blue:#edf3fb;--paper:#fff;--soft:#f5f5f3}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--soft);color:var(--ink);font-family:"Microsoft YaHei UI","Segoe UI",sans-serif;font-size:15px;line-height:1.7}a{color:inherit;text-underline-offset:4px}a:focus-visible,summary:focus-visible{outline:3px solid var(--red);outline-offset:5px}.shell{max-width:1180px;margin:auto;padding:28px 32px 54px}.top{display:flex;justify-content:space-between;gap:20px;border-bottom:2px solid var(--ink);padding-bottom:17px;font-size:13px}.brand{font-weight:800;letter-spacing:.08em}.independent{color:var(--muted)}.masthead{display:grid;grid-template-columns:1fr 300px;gap:48px;padding:44px 0 32px;align-items:center}.eyebrow{color:var(--red);font-weight:800;letter-spacing:.14em;font-size:12px;margin:0 0 10px}h1{font-family:"Arial Black","Microsoft YaHei UI",sans-serif;font-size:clamp(34px,5vw,62px);line-height:1.18;letter-spacing:-.045em;margin:0 0 17px;font-weight:900}.intro{max-width:670px;color:var(--muted);margin:0}.receipt{background:var(--yellow);padding:21px 24px;position:relative;border:1px solid var(--ink);box-shadow:5px 5px 0 var(--ink);transform:rotate(2deg)}.receipt strong{display:block;font-size:18px}.receipt small{display:block;font-size:12px;overflow-wrap:anywhere}.receipt hr{border:0;border-top:1px dashed var(--ink);margin:12px 0}.nav{display:flex;gap:9px;flex-wrap:wrap;margin:8px 0 25px}.nav a{background:white;border:1px solid var(--line);padding:8px 15px;border-radius:30px;text-decoration:none;font-size:13px}.nav a:first-child{background:var(--ink);color:white;border-color:var(--ink)}.notice{border-left:4px solid var(--red);background:#fff0ed;padding:15px 19px;margin:18px 0;color:#7a2324;font-size:14px}.notice.demo{background:var(--yellow);color:var(--ink);border-color:var(--ink)}section{margin:38px 0}h2{font-size:24px;letter-spacing:-.03em;margin:0}.sectionhead{display:flex;justify-content:space-between;gap:20px;align-items:baseline;border-bottom:1px solid var(--ink);padding-bottom:12px;margin-bottom:18px}.count{font-size:12px;color:var(--muted)}.lead{font-size:13px;color:var(--muted);margin:-6px 0 18px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:17px}.card{background:white;border:1px solid var(--line);border-radius:4px;padding:22px;min-width:0;display:flex;flex-direction:column}.card.activity{border-top:5px solid var(--yellow)}.card.product{border-top:5px solid var(--red)}.tag{font-size:11px;letter-spacing:.06em;color:var(--muted);margin:0 0 12px}.card h3{font-size:19px;line-height:1.55;margin:0 0 15px;overflow-wrap:anywhere}.phase{font-size:12px;display:inline-block;padding:4px 8px;background:var(--blue);align-self:flex-start;margin-bottom:14px}.phase.past{background:#f1edeb;color:#7d4b43}.amount{font-size:15px;font-weight:700;margin:0 0 10px}.description{font-size:13px;white-space:pre-wrap;overflow-wrap:anywhere;color:#514b43;margin:0 0 16px}.dates{font-size:12px;color:var(--muted);overflow-wrap:anywhere;margin:0 0 16px}.source{border-top:1px dashed var(--line);padding-top:12px;margin-top:auto;font-size:11px;color:var(--muted);overflow-wrap:anywhere}.source details{margin-top:5px}summary{cursor:pointer}.empty{padding:24px;background:white;border:1px dashed var(--line);font-size:14px;color:var(--muted)}.more{margin-top:25px}.more>summary{padding:15px 0;font-size:15px;font-weight:700}.more .grid{margin-top:10px}.checks{display:grid;grid-template-columns:1fr 1fr;gap:12px}.check{background:white;padding:17px;border:1px solid var(--line);font-size:13px}.check strong{display:block}.check p{color:var(--muted);margin:4px 0}.check small{color:var(--muted);overflow-wrap:anywhere}footer{border-top:2px solid var(--ink);padding-top:17px;margin-top:42px;font-size:12px;color:var(--muted);display:flex;justify-content:space-between;gap:20px} @media(max-width:900px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.masthead{grid-template-columns:1fr 250px;gap:28px}.shell{padding:24px}}@media(max-width:620px){.shell{padding:18px 16px 36px}.top{font-size:11px;gap:10px}.masthead{grid-template-columns:1fr;padding-top:30px;gap:24px}.receipt{transform:none;max-width:none;box-shadow:3px 3px 0 var(--ink)}.grid,.checks{grid-template-columns:1fr}.sectionhead{gap:10px}h2{font-size:22px}.card{padding:19px}footer{display:block}footer span{display:block;margin-bottom:8px}.nav{margin-top:20px}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}@media print{body{background:white}.shell{padding:0}.nav{display:none}.receipt{box-shadow:none;transform:none}.card{break-inside:avoid}.grid{grid-template-columns:1fr 1fr}}
'''

CSS += '''
.notice.info{border-left-color:#8097ac;background:var(--blue);color:#34485a}.notice.info strong{font-weight:600}.history{border:1px solid var(--line);border-radius:4px;background:white}.history>summary{padding:16px 20px;color:var(--muted)}.history[open]>summary{border-bottom:1px solid var(--line);color:var(--ink)}.history .lead{margin:16px 20px}.history .grid{padding:0 16px 16px}.history .card.product{border-top-color:var(--line)}
'''

TOOL_LABELS = {'mall-points-products': '商城周边查询', 'campaign-calendar': '当月活动日历', 'mall-product-detail': '商品详情查询'}
STATUS_LABELS = {'ok': '查询成功', 'empty': '本次返回为空', 'failed': '查询失败', 'needs_input': '需要补充参数', 'unsupported': '暂无法解释'}


def e(value) -> str:
    return escape(str(value), quote=True)


def card_html(card: Card) -> str:
    activity = card.source_tool == 'campaign-calendar'
    price = '' if activity else '<p class="amount">' + e(card.points if card.points is not None else '接口未提供') + ' 积分 · ¥' + e(card.cash if card.cash is not None else '接口未提供') + '</p>'
    url = safe_url(card.source_url)
    link = f'<p><a href="{e(url)}" target="_blank" rel="noopener noreferrer">查看原始说明 ↗</a></p>' if url else ''
    item = f'<br>商品编号：{e(card.item_id)}（用于选择详情）' if card.item_id is not None else ''
    past = ' past' if card.phase == '已过接口展示期限' else ''
    return f'''<article class="card {'activity' if activity else 'product'}">
<p class="tag">{e(card.kind)}</p><h3>{e(card.title)}</h3>
<span class="phase{past}">{e(card.phase)}</span>{price}
<p class="description">{e(card.description or '接口未提供参与说明')}</p>
<p class="dates">{e(card.dates or '接口未提供时间信息')}</p>{link}
<div class="source">来源：{e(TOOL_LABELS.get(card.source_tool, '查询结果'))}<details><summary>查看来源信息</summary>{e(card.source_tool)}{item}<br>兑换资格、库存及完整规则请在麦当劳官方渠道核实。</details></div></article>'''


def render_report(results: list[QueryResult], cards: list[Card], *, demo: bool = False) -> str:
    if results and all(r.tool == 'mall-product-detail' for r in results):
        return render_detail_report(results, cards, demo=demo)
    merch = [c for c in cards if c.source_tool != 'campaign-calendar']
    history = [c for c in merch if c.phase == '已过接口展示期限']
    nonhistory = [c for c in merch if c.phase != '已过接口展示期限']
    in_period = [c for c in nonhistory if c.phase == '接口展示期内 · 库存未核实']
    pending_count = len(nonhistory) - len(in_period)
    events = [c for c in cards if c.kind == '周边活动线索']
    other = [c for c in cards if c.source_tool == 'campaign-calendar' and c.kind != '周边活动线索']
    bad = any(r.status not in {'ok', 'empty'} for r in results)
    stamp = max((r.queried_at for r in results if r.queried_at), default='时间未提供')
    notice = '<div class="notice demo"><strong>虚构样例</strong> · 用于预览报告，不代表真实商品、活动或接入结果。</div>' if demo else ''
    if bad:
        notice += '<div class="notice" role="alert"><strong>部分查询未完成</strong> · 下方保留成功结果；失败来源请看“查询说明”。</div>'
    if history and not nonhistory:
        notice += f'<div class="notice info" role="status"><strong>本次商城查询仅返回 {len(history)} 条历史周边，暂未发现展示期内的商品。</strong> 历史记录已收起，点击“历史周边”可展开；近期活动线索见下方。本次结果不代表官方商城的全部商品。</div>'

    def grid(items, empty):
        return '<div class="grid">' + ''.join(card_html(c) for c in items) + '</div>' if items else '<p class="empty">' + e(empty) + '</p>'

    checks = ''.join(f'<div class="check"><strong>{e(TOOL_LABELS.get(r.tool,r.tool))} · {e(STATUS_LABELS.get(r.status,r.status))}</strong><p>{e(r.message or "仅展示本次返回范围。")}</p><small>{e(r.queried_at)} · 覆盖范围：{e({"complete":"已确认完整","partial":"部分返回","unknown":"未确认完整"}.get(r.coverage,r.coverage))}</small></div>' for r in results)
    more = '<details class="more"><summary>其他活动 · ' + str(len(other)) + ' 条</summary>' + grid(other, '') + '</details>' if other else ''
    history_html = '<details class="more history" id="history"><summary>历史周边 · ' + str(len(history)) + ' 条（点击展开）</summary><p class="lead">以下商品已过接口返回的展示期限，仅保留历史信息，不能据此认定现在可兑换。</p>' + grid(history, '') + '</details>' if history else ''
    merch_empty = '本次返回的商品均为历史记录，可展开下方查看。当前库存及其他商品请到官方 App 核实。' if history else '本次没有可展示的商城记录，请查看查询说明；这不代表商城没有周边。'
    receipt_merch = f'展示期内 {len(in_period)} 条 · 历史周边 {len(history)} 条'
    if pending_count:
        receipt_merch += f' · 其他待确认 {pending_count} 条'
    merch_count = f'本次返回 {len(merch)} 条' + (' · 含历史记录' if history else '')
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>麦麦周边雷达 · 查询报告</title><style>{CSS}</style></head><body><main class="shell">
<header class="top"><span class="brand">麦麦周边雷达</span><span class="independent">独立参赛项目 · 非官方应用</span></header>
<div class="masthead"><div><p class="eyebrow">周边与活动 · 一次看清</p><h1>周边与活动查询结果</h1><p class="intro">查看本次返回的商品和当月活动线索。历史周边单独收起；参与前请核对时间、完整规则和官方渠道的当前状态。</p></div><aside class="receipt"><strong>本次查询回执</strong><hr><small>{e(stamp)}</small><small>{e(receipt_merch)}</small><small>周边活动线索 {len(events)} 条</small><small>{'虚构样例' if demo else '真实接口返回 · 仅供查询参考'}</small></aside></div>
<nav class="nav" aria-label="报告导航"><a href="#events">活动线索 {len(events)}</a><a href="#merch">商城周边 {len(merch)}</a><a href="#sources">查询说明</a></nav>{notice}
<section id="events"><div class="sectionhead"><h2>周边活动线索</h2><span class="count">{len(events)} 条合并记录</span></div><p class="lead">按标题与说明中的周边、联名、玩具等关键词整理，可能包含非周边活动或遗漏。日历展示日期不等于活动完整起止时间。</p>{grid(events,'本次没有识别到周边活动线索；请同时查看其他活动与查询状态。')}{more}</section>
<section id="merch"><div class="sectionhead"><h2>商城周边</h2><span class="count">{e(merch_count)}</span></div><p class="lead">已使用接口提供的周边类目筛选。展示期限未过或时间尚未确认的记录优先显示，过期记录收在“历史周边”中。积分、现金、库存及兑换资格以官方页面为准。</p>{grid(nonhistory,merch_empty)}{history_html}</section>
<section id="sources"><div class="sectionhead"><h2>查询说明</h2><span class="count">信息有边界，判断更清楚</span></div><div class="checks">{checks}</div></section>
<footer><span>麦麦周边雷达 · 本机生成的静态报告<br>不会执行兑换、下单或活动报名。</span><span>发现内容感兴趣？在官方 App 核对完整规则后自行参与。<br><a href="https://open.mcd.cn/mcp" target="_blank" rel="noopener noreferrer">数据能力来源 ↗</a></span></footer>
</main></body></html>'''


def render_detail_report(results: list[QueryResult], cards: list[Card], *, demo: bool = False) -> str:
    stamp = max((r.queried_at for r in results if r.queried_at), default='时间未提供')
    title = '商品详情' if cards else '未能取得商品详情'
    demo_note = '<div class="notice demo">虚构样例，不代表真实商品或接口结果。</div>' if demo else ''
    checks = ''.join(
        f'<div class="check"><strong>商品详情查询 · {e(STATUS_LABELS.get(r.status, r.status))}</strong>'
        f'<p>{e(r.message or "仅展示本次详情返回范围。")}</p><small>{e(r.queried_at)} · 来源：{e(r.tool)}</small></div>'
        for r in results
    )
    content = ''.join(detail_card_html(card) for card in cards) if cards else '<p class="empty">接口没有返回可展示的详情资料。请查看上面的具体原因；不能据此推断其他商品的情况。</p>'
    extra_css = '.detailcard{margin-top:20px}.detailcard h3{font-size:26px}.detailcard h4{margin:20px 0 8px}.specs{overflow-x:auto}.specs table{border-collapse:collapse;min-width:460px;width:100%;font-size:13px}.specs th,.specs td{text-align:left;padding:12px;border-bottom:1px solid var(--line)}.specs th{background:var(--soft)}.detailcard .description{line-height:1.9}.image-links{display:flex;gap:18px;flex-wrap:wrap;font-size:13px}'
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>麦麦周边雷达 · 商品详情</title><style>{CSS}{extra_css}</style></head><body><main class="shell">
<header class="top"><span class="brand">麦麦周边雷达</span><span class="independent">独立参赛项目 · 非官方应用</span></header>
<div class="masthead"><div><p class="eyebrow">商品详情 · 单独查询记录</p><h1>{title}</h1><p class="intro">本次只查询选定商品的详情。详情记录单独保存，原有周边与活动总览保持不变。</p></div><aside class="receipt"><strong>详情查询回执</strong><hr><small>{e(stamp)}</small><small>{'虚构样例' if demo else '实际接口查询记录'}</small></aside></div>
{demo_note}<section><div class="sectionhead"><h2>本次查询结果</h2></div><div class="checks">{checks}</div>{content}</section>
<nav class="nav"><a href="../radar.html">返回已有的周边与活动总览</a></nav>
<footer><span>查询结果不代表库存、兑换资格或报名状态。</span><span>未执行下单、兑换或任何其他业务写入。</span></footer>
</main></body></html>'''


def detail_card_html(card: Card) -> str:
    voucher = card.kind == '餐券详情（非周边）'
    notice = '<div class="notice">兑换餐券不等于免费获得餐品。请核对使用须知中的后续消费金额与券面有效期。</div>' if voucher else ''
    unknown = '接口未提供'
    def amount(value):
        return e(value if value is not None else unknown)
    rows = ''.join(f'<tr><td>规格 {index} · 编号 {amount(s.item_id)}</td><td>{amount(s.points)}</td><td>{amount(s.cash)}</td><td>{amount(s.trade_price)}</td></tr>' for index, s in enumerate(card.skus, 1))
    trade_label = '用券消费金额参考*' if voucher else '其他金额字段*'
    specs = f'<div class="specs"><table><thead><tr><th scope="col">规格</th><th scope="col">兑换积分</th><th scope="col">接口兑换金额（元）</th><th scope="col">{trade_label}</th></tr></thead><tbody>{rows}</tbody></table></div>' if rows else '<p class="empty">接口未提供可展示的规格。</p>'
    images = ''.join(f'<a href="{e(url)}" target="_blank" rel="noopener noreferrer">查看商品图片 {i} ↗</a>' for i, raw in enumerate(card.image_urls, 1) if (url := safe_url(raw)))
    return f'''<article class="card detailcard"><p class="tag">{e(card.kind)}</p><h3>{e(card.title)}</h3><span class="phase">{e(card.phase)}</span><p class="description">{e(card.description or '接口未提供简要说明')}</p><p class="dates">{e(card.dates or '接口未提供时间信息')}</p>{notice}<h4>规格与金额</h4>{specs}<p class="lead">* 该列对应服务返回的 extTradePrice，具体含义与应付条件请核对商品使用须知，不作最终结算保证。</p><h4>使用须知</h4><p class="description">{e(card.notes or '接口未提供使用须知')}</p><h4>商品说明</h4><p class="description">{e(card.detail_text or ('接口详情包含图片，可点击下方链接查看。' if card.image_urls else '接口未提供文字详情'))}</p><div class="image-links">{images}</div><div class="source">来源：{e(card.source_tool)} · 商品编号：{e(card.item_id if card.item_id is not None else unknown)}。未执行兑换或下单。</div></article>'''


def write_report(html: str, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding='utf-8')
    return output
