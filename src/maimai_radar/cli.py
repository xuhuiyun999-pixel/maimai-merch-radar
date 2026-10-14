import argparse
import asyncio
import getpass
import json
import webbrowser
from dataclasses import asdict
from pathlib import Path

from .config import LocalInputError, load_token, project_root
from .mcp_client import READONLY_TOOLS, collect, discover_tools, now
from .models import QueryResult
from .normalize import normalize
from .report import render_report, write_report


def save_results(root: Path, results, cards, *, demo: bool = False) -> Path:
    detail_only = bool(results) and all(r.tool == 'mall-product-detail' for r in results)
    folder = root / 'output' / ('demo' if demo else 'details' if detail_only else '')
    path = write_report(render_report(results, cards, demo=demo), folder / 'radar.html')
    metadata = [{k: v for k, v in asdict(r).items() if k != 'payload'} for r in results]
    (folder / 'radar.json').write_text(json.dumps({'demo': demo, 'queries': metadata, 'cards': [asdict(c) for c in cards]}, ensure_ascii=False, indent=2), encoding='utf-8')
    return path


def fail_safely(args, root: Path, message: str) -> int:
    print(message)
    if args.command == 'query':
        names = [args.tool] if args.tool else ['mall-points-products', 'campaign-calendar']
        results = [QueryResult(name, 'failed', queried_at=now(), message=message) for name in names]
        try:
            path = save_results(root, results, [])
            print('本次失败状态已写入报告，旧结果已替换：' + str(path))
        except Exception:
            print('报告无法更新；旧文件不能作为本次查询结果。')
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description='麦麦周边雷达：只读查询')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('configure', help='在本机隐藏输入连接凭据')
    commands.add_parser('discover', help='确认只读查询工具与输入结构')
    query = commands.add_parser('query', help='查询周边和活动并生成本地报告')
    query.add_argument('--tool', choices=sorted(READONLY_TOOLS))
    query.add_argument('--arguments-file', type=Path, help='已确认的查询参数 JSON 文件')
    query.add_argument('--open', action='store_true', help='生成后打开浏览器')
    demo = commands.add_parser('demo', help='生成显著标记为虚构的样例报告')
    demo.add_argument('--open', action='store_true')
    args = parser.parse_args()
    root = project_root()
    try:
        if args.command == 'configure':
            token = getpass.getpass('请粘贴 MCP Token（输入不显示）：').strip()
            if not token or '\n' in token or '\r' in token:
                raise LocalInputError('凭据格式无效，请重新配置。')
            (root / '.env').write_text('MCD_MCP_TOKEN=' + token + '\n', encoding='utf-8')
            print('本机配置已保存，凭据未显示。')
            return 0
        if args.command in {'query', 'demo'}:
            is_demo = args.command == 'demo'
            if is_demo:
                from .demo import demo_data
                results, cards = demo_data()
            else:
                if args.arguments_file and not args.tool:
                    raise LocalInputError('使用参数文件时请同时指定 --tool。')
                requests = {'mall-points-products': {'catRuleIds': '2>8'}, 'campaign-calendar': {}}
                if args.tool:
                    arguments = json.loads(args.arguments_file.read_text(encoding='utf-8-sig')) if args.arguments_file else {}
                    if not isinstance(arguments, dict):
                        raise LocalInputError('参数文件必须是 JSON 对象。')
                    requests = {args.tool: arguments}
                results = asyncio.run(collect(load_token(root), requests))
                cards = [card for result in results for card in normalize(result)]
            path = save_results(root, results, cards, demo=is_demo)
            print('虚构样例报告已生成。' if is_demo else '查询报告已生成。')
            for result in results:
                print(f'{result.tool}: {result.status} — {result.message}')
            print(str(path))
            if args.open:
                webbrowser.open(path.as_uri())
            return 0 if all(r.status in {'ok', 'empty'} for r in results) else 1
        tools = asyncio.run(discover_tools(load_token(root)))
        private = root / 'private'
        private.mkdir(exist_ok=True)
        (private / 'tools.json').write_text(json.dumps(tools, ensure_ascii=False, indent=2), encoding='utf-8')
        for name in sorted(READONLY_TOOLS):
            print(f'{name}: ' + ('可用' if name in tools else '服务未提供'))
        print('输入结构已保存到本机 private/tools.json。')
        return 0 if READONLY_TOOLS.issubset(tools) else 1
    except LocalInputError as exc:
        return fail_safely(args, root, str(exc))
    except Exception:
        return fail_safely(args, root, '输入或连接未成功；请检查参数文件、网络和凭据，配置值未显示。')


if __name__ == '__main__':
    raise SystemExit(main())
