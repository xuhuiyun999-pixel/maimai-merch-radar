# 麦麦周边雷达

把麦当劳商城周边与当月活动整理成一份中文报告，帮助想了解周边、联名及活动条件的用户少翻几页信息。

这是基于麦当劳 MCP 的独立参赛项目，非官方应用。第一版只查询信息，不兑换、不下单、不抽奖、不领券、不报名。

**先看示例 → [无需 Token 的结果示例](examples/DEMO.md)** · **开始试用 → [下载完整项目](https://github.com/xuhuiyun999-pixel/maimai-merch-radar/archive/refs/heads/main.zip)** · **[安装步骤](#安装)**

## 它适合解决什么问题

| 你想了解 | 这个项目会整理什么 |
| --- | --- |
| 最近有什么周边或联名活动？ | 周边类目商品、当月活动中的周边线索及原始说明 |
| 一件周边需要多少积分或现金？ | 接口明确返回的积分、现金字段与展示期限，缺失内容标明未知 |
| 为什么列表里有商品，详情却看不到？ | 保留“商品已下架”等真实失败状态，避免把历史记录当作当前可兑换 |

没有编程经验也可以先阅读示例；运行真实查询需要 Python 3.12+ 和你自己的麦当劳 MCP Token。结果保存在本机，不需要额外购买模型 API 服务。

## 已能运行的流程

“最近有什么麦当劳周边和活动？” → 真实查询周边类目与当月日历 → 整理参与说明、积分/现金字段、日期与来源 → 生成本地报告。

- 已真实验证商城周边列表与活动日历。详情已验证成功与下架两条路径：成功样本为餐券（明确标为非周边），下架样本为历史周边。尚未取得可用周边的成功详情，不能据此确认周边库存。
- 周边活动线索采用关键词归类，可能有误收和遗漏；其他活动也保留在报告中。
- 商城可能返回过期记录，报告会明确标注“已过接口展示期限”。展示期内也不等于库存或兑换资格已核实。
- 日历日期是日历展示日期，不能直接视为完整活动期限。接口没有明确总量或分页结束标记时，只声称展示本次返回范围。

## 安装

需要 Python 3.12 或更新版本。先下载上方 ZIP 并解压，在解压后的项目文件夹中打开 PowerShell，再逐行执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m maimai_radar.cli configure
```

Token 在[麦当劳 MCP 官网](https://open.mcd.cn/mcp)登录后申请。`configure` 隐藏输入，只写入本机 `.env`，不需要把 Token 发到聊天或写进代码。也可由执行环境设置 `MCD_MCP_TOKEN`，环境变量优先。

安装不需要激活脚本或修改 PowerShell 执行策略。依赖只装在项目 `.venv`；当前使用官方 Python SDK `mcp==1.30.0`。

## 使用

双击 `启动雷达.cmd`：查询真实数据，生成并尝试用本机默认浏览器打开报告。

也可在项目目录运行：

```powershell
.\.venv\Scripts\python.exe -m maimai_radar.cli discover
.\.venv\Scripts\python.exe -m maimai_radar.cli query
```

结果在 `output/radar.html` 和 `output/radar.json`。HTML 可直接在本机浏览器打开，不需要公网网站或模型 API Key。JSON 只保留整理后的卡片和查询状态，不导出原始会员数据。`query --open` 可尝试打开默认浏览器。

命令返回非零表示查询或适配有未完成部分；即使生成了报告，也应查看每个来源的状态。

商品详情查询单独写入 `output/details/radar.html` 与 `output/details/radar.json`，不会覆盖总览。先从真实列表选定商品编号，按 `discover` 返回的输入结构将整数 `spuId` 写入本机参数文件，再执行：

```powershell
.\.venv\Scripts\python.exe -m maimai_radar.cli query --tool mall-product-detail --arguments-file .\private\detail-arguments.json
```

成功详情展示全部返回规格、兑换积分、接口兑换金额、其他金额字段及使用须知；餐券单独提示使用时可能仍需付款，不把“兑换金额为 0”解释成免费餐品。富文本转为文字，图片只提供手动打开的链接。接口返回“商品已下架”时，报告显示具体原因并返回失败状态；未知结构仍标为暂无法解释。

```powershell
# 虚构样例，单独写入 output/demo，不会覆盖真实报告
.\.venv\Scripts\python.exe -m maimai_radar.cli demo

# 运行本地测试，不会联网
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

从其他工作目录调用时，对 Python 可执行文件使用带引号的绝对路径并前置 `&`；助手通过源码位置定位项目，不依赖当前目录。启动器的 `--check` 模式只生成真实报告，不打开浏览器、不等待按键，便于验证。

## 在 AI 客户端中使用技能

技能位于 `skills/maimai-merch-radar/SKILL.md`。保留完整项目，让支持读取项目技能文件和运行本地命令的 AI 客户端加载该文件，然后提问：

> 使用这个项目中的 maimai-merch-radar 技能，看看最近有什么麦当劳周边和活动，并告诉我哪些信息还未核实。

技能将调用本地查询助手并读取报告。不同客户端的技能导入方式不同；本项目没有声称已验证每一种客户端的自动安装。可以先明确提供技能文件路径进行项目内使用。

`mcp-config.example.json` 是脱敏连接说明，使用 `${MCD_MCP_TOKEN}` 占位符。能否自动展开变量取决于客户端；不能假定所有客户端都可直接复制运行。本项目查询助手直接读取环境变量或私密 `.env`，无需展开这个 JSON。

## 数据与发布

`.env`、`private/`、`output/`、`.venv/` 已排除在 Git 范围外。不要把它们作为附件或公开文件上传。公开发布前另行检查 Git 暂存内容。

参赛文件包括本 README、官方原文 `CONTEST_DECLARATION.md`、`MCP_INTEGRATION.md`、脱敏配置示例和技能/源码。没有真实使用 WorkBuddy，因此没有提交 `workbuddy.md`，也不申领其专项奖励。

项目源码已公开发布到 [xuhuiyun999-pixel/maimai-merch-radar](https://github.com/xuhuiyun999-pixel/maimai-merch-radar)。浏览器自动视觉验证受到工具的本地文件访问策略限制，布局仍需本人在本机浏览器确认。报名状态以官方活动仓库中的报名 Issue 回复为准；源码公开不等于报名或获奖审核通过。

详情见 [MCP_INTEGRATION.md](MCP_INTEGRATION.md) 和[官方比赛规则](https://github.com/M-China/mcd-developer-innovation-challenge/blob/main/activityGuidelines.md)。

## 反馈与支持

欢迎在 [Issues](https://github.com/xuhuiyun999-pixel/maimai-merch-radar/issues) 反馈安装、使用或结果解释上的问题。请说明你执行了哪条命令、看到什么提示；不要提交 Token、`.env` 或原始会员数据。

如果这个项目对你有用，欢迎给仓库一个 Star，让更多有相同需求的人发现它。
