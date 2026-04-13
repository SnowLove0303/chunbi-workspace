# MEMORY.md - 长期记忆

## 关于我自己

- **名字:** 春笔 ✒️
- **上线日期:** 2026-04-02

## 关于用户

- 通过飞书联系
- 在 Windows 上使用 Obsidian
- Vault 路径:`C:\Users\chenz\Documents\Obsidian Vault`
- 尚未告知我他的名字

## Obsidian 排版 Skill（2026-04-05）
- **ZIP 路径**：`F:\skill\排版\obsidian-format-skill.zip`
- **Skill 目录**：`F:\skill\排版\obsidian-format-skill\`
- **内容**：SKILL.md(9.8KB) + REFERENCES.md + 6个Templater模板 + skill.json
- **GitHub 来源**：SilentVoid13/Templater, blacksmithgu/Dataview, tgrosinger/Advanced-Tables 等
- **模板**：通用/日记/读书笔记/卡片笔记/项目笔记/每日回顾

## 已安装 Skills

| 编号 | 名称 | 路径 | 状态 |
|------|------|------|------|
| #1 | obsidian | `workspace/skills/obsidian/` | ✅ 可用 |
| #2 | search-layer | `workspace/skills/search-layer/` | ✅ Tavily 已配置 |
| #3 | content-extract | `workspace/skills/content-extract/` | ✅ 可用 |
| #4 | mineru-extract | `workspace/skills/mineru-extract/` | ⚠️ 待配置 MinerU |
| #5 | coding-agent | `workspace/skills/coding-agent/` | ⚠️ 需本地 CLI 工具 |
| #6 | pr-reviewer | `workspace/skills/pr-reviewer/` | ⚠️ 需 gh CLI |
| #7 | opencode-lark | `C:\Users\chenz\AppData\Roaming\npm\node_modules\opencode-lark` | ✅ 飞书集成工作中 |
| #8 | adb | `C:\Users\chenz\.openclaw\workspace\skills\adb` | ✅ Skill + MCP Server 已安装 |
| #9 | clawpaw-android-control | `GitHub: klscool/clawpaw-android-control` | ⏳ 待部署(需公网 Gateway) |
| #10 | video-news-workflow | `skills/video-news-workflow/` | ✅ 统一工作流(获取视频→转录→笔记) |
| #11 | openclaw-optimization-guide | `workspace/skills/openclaw-optimization-guide/` | ✅ 已安装(README 指南 + 优化模板) |
| #12 | Workflow-coze_seedance15pro | `workspace/skills/Workflow-coze_seedance15pro/` | ✅ Coze Workflow(视频生成) |
| #13 | video-workflow | `workspace/skills/video-workflow/` | ⚠️ 全链路视频处理(ffmpeg 待安装) |
| #14 | faster-whisper | `workspace/skills/faster-whisper/` | ✅ 语音转文字(Whisper fast) |
| #15 | CoPaw | `C:\Users\chenz\AppData\Roaming\Python\Python313\Scripts\copaw.exe` | ✅ v1.0.0,端口 8088,NVIDIA NIM + MiniMax M2.5 已配置 |
| #16 | bilibili-news | `F:\skill\bilibili-news.zip` | ⚠️ 已废弃，内容合并到 #10 |
| #17 | PyQt-Fluent-Widgets | `pip install PyQt-Fluent-Widgets` | ✅ PyQt5 v1.11.2（已有）|
| #18 | PyQt6-Fluent-Widgets | `pip install PyQt6-Fluent-Widgets` | ✅ PyQt6 v1.11.2，已安装 PyQt6-Frameless-Window 0.8.1，源码 ZIP 存于 `F:\skill\PyQt6-Fluent-Widgets.zip` |
| #19 | github-search | `openclaw-skills/skills/github-search/` | ✅ 免API，`gh search`驱动 |
| #20 | github-explorer | `openclaw-skills/skills/github-explorer/` | ✅ 免API，`gh api`驱动 |
| #21 | gitclaw-backup | `openclaw-skills/skills/gitclaw-backup/` | ✅ 自动同步脚本 |

## 环境状态

- **Python:** `C:\Users\chenz\AppData\Local\Programs\Python\Python313\python.exe` (3.13.12)
- **pip 镜像:** 阿里云镜像 `https://mirrors.aliyun.com/pypi/simple/`

## Obsidian 信息

- Vault:`C:\Users\chenz\Documents\Obsidian Vault`
- Skill 笔记:`C:\Users\chenz\Documents\Obsidian Vault\skill\`
- 配置:`%APPDATA%\obsidian\obsidian.json`
- 当前版本:**1.12.7**
- obsidian-cli 在 Windows 上支持有限,优先使用直接文件操作

## OpenCode + 飞书环境

- **GUI:** `F:\AI\opencode\OpenCode.exe`
- **CLI:** `F:\AI\opencode\opencode-cli.exe`
- **opencode-lark:** `C:\Users\chenz\AppData\Roaming\npm\node_modules\opencode-lark`(版本 0.2.0)
- **ngrok 隧道:** `https://scarlett-threadless-ninthly.ngrok-free.dev`
- **当前状态:** `opencode serve` + `opencode-lark` 运行中
- **配置文件:**
  - `C:\Users\chenz\.config\opencode\opencode.json`
  - `C:\Users\chenz\.config\opencode-lark\.env.cli_a9434362cf395cd4`

### Oh My OpenCode(已安装)
- 安装方式:`bunx oh-my-opencode install --no-tuner --claude=no --openai=no --gemini=no --copilot=no`
- 激活命令:`ultrawork` 或 `ulw`
- 版本:1.3.13(bundled binary)
- 配置文件:`F:\openclaw1\.config\opencode\opencode.json`

## ADB 环境

- **ADB 路径:** `F:\WSL\platform-tools\adb.exe`
- **MCP Server:** `openclaw-adb-mcp`(npm 全局安装)
- **Skill:** `C:\Users\chenz\.openclaw\workspace\skills\adb`
- **手机连接:** USB 调试模式,设备 ID 通过 `adb devices` 获取

## AI 开发指南(Obsidian)

已在 `C:\Users\chenz\Documents\Obsidian Vault\AI开发指南\` 建立以下笔记:
- **CrewAI开发指南.md**(详细,19KB+)
- **CoPaw.md**(详细,8KB+)
- **ClawTeam-OpenClaw开发指南.md**(乱码文件名但 Obsidian 可读)

已在 `C:\Users\chenz\Documents\Obsidian Vault\开发项目ing\` 建立以下笔记:
- **ClawTeam-OpenClaw.md**
- **CoPaw.md**(开发项目版,6KB+)

## CoPaw（已安装）

- **GitHub:** agentscope-ai/CoPaw（14,355 stars）
- **安装路径:** `C:\Users\chenz\AppData\Roaming\Python\Python313\Scripts\copaw.exe`
- **工作目录:** `C:\Users\chenz\.copaw`
- **Web UI:** `http://127.0.0.1:8088/`
- **内置 Agent:** default + CoPaw_QA_Agent_0.1beta1
- **启动脚本:** `F:\openclaw1\.openclaw\workspace\CoPaw启动.bat`
- **飞书渠道:** config.json 中可配置，需填 app_id / app_secret

### CoPaw Providers（2026-04-04）
| Provider | API Key | 免费模型 |
|----------|---------|----------|
| nvidia-nim | `nvapi-...` | MiniMax M2.5, DeepSeek R1 |
| openrouter | `sk-or-v1-...` | MiniMax M2.5:free, STEP 3.5 Flash:free |

- Provider 配置: `C:\Users\chenz\.copaw\providers\custom\`
- .env 配置: `C:\Users\chenz\.copaw\.env`

## VNpy 数据源情况（2026-04-04）
- **vnpy_tushare: ✅ 已安装**（Token: `760b232dbead033e456e13ab3a928e9f7c8874dc51eb1c2177f2dbf5`）
- **akshare: ✅ 已安装**（1.18.51，免费无需Token）
- **vnpy_tdx (hxtrade版): ✅ GitHub安装**（来源: https://github.com/hxtrade/vnpy_tdx）
  - 依赖 mootdx（已装）+ cn_stock_holidays（已装）
  - mootdx用在线服务器（深圳/上海/北京/广州主站 IP:7709），无需本地TDX文件
  - **VNpy全局配置已生效**: `C:\Users\chenz\.vntrader\vt_setting.json` → `datafeed.name = "tdx"`
  - REST API（端口9999）自动加载 TDX，已验证60条K线
  - 已修复：mootdx/pandas3.0兼容性、`is_trading_day`补丁、numpy JSON序列化
  - ⚠️ mootdx强制httpx==0.25.2，与copaw/fastmcp等冲突（httpx>=0.28.1）
  - PyPI上的vnpy_tdx（bthuntergg版）仍是坏的，只有元数据无代码

## OpenClaw 模型配置(2026-04-04 更新)

### Providers
| Provider | 模型数 | 说明 |
|----------|--------|------|
| minimax | 1 | 主用,官方付费 |
| kimi | 1 | 备用 |
| nvidia | 6 | 免费备用 |
| openrouter | 2 | 免费备用 |

### 免费模型
- **OpenRouter**: MiniMax M2.5:free, STEP 3.5 Flash:free
- **NVIDIA**: MiniMax M2.5, Llama 4 Maverick, Gemma 4, DeepSeek R1

### 默认模型
- **primary**: minimax/MiniMax-M2.7
- **fallbacks**: openrouter/minimax/minimax-m2.5:free, nvidia/minimaxai/minimax-m2.5

### API Keys
- minimax: sk-cp-...
- kimi: sk-kimi-...
- nvidia: nvapi-K39...
- openrouter: sk-or-v1-...

### 配置文件
- 主配置: `F:\openclaw\openclaw.json`
- 认证配置: `F:\openclaw\agents\main\agent\auth-profiles.json`
- 详细文档: `Obsidian: AI开发指南/OpenClaw模型配置.md`

---

## 实时快报任务（2026-04-09 重大更新）

### 最新工作流（2026-04-09 确立）

```
OpenCLI接管Chrome → 拿BV号 → yt-dlp下载音频 → Whisper转录 → 理解内容 → 手动整理格式 → 保存
```

**关键突破**：B站 Space API 对橘郡Juya UID 返回 -799/412 永久限流。解决方案：
1. **OpenCLI** (`@jackwener/opencli`) 接管用户 Chrome 浏览器，读取空间页面拿 BV 号
2. yt-dlp 用已有 cookies 下载音频
3. Whisper 转录
4. **手动理解转录内容，按标准格式整理**（见下方）
5. 保存到 Obsidian

### 日报标准格式（2026-04-09 确立）

**不直接堆转录内容**，而是理解后分类整理：

```
## 今日头条（2-3条最重要）
### [标题]
[正文1-2段，背景+结论]

## 大厂动态
### 公司 — [产品/事件名]
[正文]

## 模型发布
### 模型名 — [一句话描述]
[正文]

## 工具更新
### 工具名 — [更新内容]
[正文]

## 行业与投资
[融资、人事变动、基准测试等]
```

### 配置
- **OpenCLI**: `npm install -g @jackwener/opencli`
- **OpenCLI命令**: `opencli operate open <url>` / `opencli operate state` / `opencli operate eval <js>`
- **UP主UID**: 橘郡Juya(285286947) / 初芽Sprout(1638385490)
- **Cookies**: `F:\工作区间\ai_news_temp\cookies.txt`
- **输出**: `C:\Users\chenz\Documents\Obsidian Vault\实时快报\`

### 脚本位置
- 转录脚本: `F:\工作区间\ai_news_temp\transcripts_clean.py`（生成标准格式日报）
- Whisper转录: `python faster-whisper`（medium模型）
- 早报模板: 直接在脚本里写 Markdown，不要用 note_formatter（它会把转录直接堆上去）

### ⚠️ B站 API 限流说明

- Space API (`/x/space/arc/search`): 橘郡Juya 永久 -799（IP+UID服务端配额）
- yt-dlp 直接下载: 同样 412
- **唯一解法**: OpenCLI 接管 Chrome（复用登录态）
- curl_cffi 可以绕过 412 反爬，但 -799 是服务端封的无法绕过

---

## 重要！用户习惯
- **找东西必须写成 Obsidian 笔记**，不只是聊天回复
- Obsidian 路径：`C:\Users\chenz\Documents\Obsidian Vault\`
- AI开发指南放 `AI开发指南\`，开发项目放 `开发项目ing\`

## THS同花顺自动化
- **控制器**: `F:\量化封存\量化系统\Strategies\ths_controller.py`（完整版）
- **备用**: `F:\量化封存\量化系统\QuantDesk_System\connectors\ths_trade.py`（PyAutoGUI版）
- **REST API**: `F:\量化封存\量化系统\ths_trade-main\`（Tornado异步框架）
- **原理**: win32gui直接发消息操作THS标准控件 + SendInput绕过消息队列
- **主窗口**: HWND=68228, 类名 Afx:MFC, 大小1440x754
- **版本**: 9.50.71（Chromium + MFC混合）
- **股票代码输入框**: EDIT HWND=4263784
- **支持**: 买入/卖出下单(写代码→Tab→写价格→Tab→写数量→Enter)
- **THS路径**: `E:/ths/同花顺/hexin.exe`
- **调试截图**: `F:\量化封存\量化系统\Strategies\ths_*.png`（~20张）

### THS菜单结构（2026-04-10摸透）
- **主菜单**: hMenu=68238, 11个菜单项
- **菜单路径**: 行情(index 2) → 板块(index 8) → 行业板块涨跌幅排名
- **行业板块涨跌幅排名**: WM_COMMAND ID=33366（快捷键800）
- **概念板块**: WM_COMMAND ID=37726
- **近期强势**: WM_COMMAND ID=38109
- **控制器**: `F:\量化封存\量化系统\Strategies\ths_controller.py`（完整版）
- **备用**: `F:\量化封存\量化系统\QuantDesk_System\connectors\ths_trade.py`（PyAutoGUI版）
- **REST API**: `F:\量化封存\量化系统\ths_trade-main\`（Tornado异步框架）
- **原理**: win32gui直接发消息操作THS标准控件 + SendInput绕过消息队列
- **主窗口**: HWND=2428586, 类名 Afx:MFC, 大小1934x1046
- **版本**: 9.50.71（Chromium + MFC混合）
- **股票代码输入框**: EDIT HWND=4263784
- **支持**: 买入/卖出下单(写代码→Tab→写价格→Tab→写数量→Enter)
- **THS路径**: `E:/ths/同花顺/hexin.exe`
- **调试截图**: `F:\量化封存\量化系统\Strategies\ths_*.png`（~20张）

## 量化策略（2026-04-04 新增）
- **策略目录**: `F:\量化\Strategies\`
- **London Breakout**: 参考时段突破，30分钟强制平仓
- **Dual Thrust**: 日内区间突破，量能确认
- **Momentum Breakout**: N高点突破+放量，追踪止损
- **Supertrend Reversal**: ATR动态止损，指标变色即行动
- **Level2 OFI**: 订单失衡，OFI>0.6大单买入，5分钟超短持仓
- **双均线优化版**: 加RSI过滤+ATR过滤+追踪止损+超短持仓
- 详见: `F:\量化\Strategies\优化说明.md`

## 量化项目（QuantDesk）

**项目路径：** `F:\量化\QuantDesk`（待创建）
**VNpy 项目路径：** `F:\量化\VNpy`（已创建，git 已提交）
**文档路径：** `C:\Users\chenz\Documents\Obsidian Vault\开发项目ing\量化\`

### 真实目录名（非中文显示名）
- `F:\HFTX` = `F:\量化`（量化系统主目录）
- `F:\QSPT` = `F:\应用级开发`（独立项目目录）

### 文档清单
| 文档 | 大小 | 说明 |
|------|------|------|
| `量化-完整部署与使用手册.md` | 19KB | 完整手册（核心文档）|
| `量化-A股可视化交易方案.md` | 17KB | 技术选型研究+参考项目 |
| `量化-快速上手.md` | 2KB | 5分钟入门精炼版 |
| `量化系统-数据来源总览.md` | 5KB | AkShare/TuShare/MooTDX/VNpy REST 数据源整理 |
| `量化系统-AkShare接口清单.md` | 18KB | AkShare 1087个接口完整分类 |
| `量化系统-AkShare字段名清单.md` | 13KB | 各接口返回的中文字段名 |

**整理后的路径：** `已开发项目/量化/00-索引/README.md`（统一入口，8个子目录，40个文档）|

### 技术选型
- UI：PyQt5 + PyQt-Fluent-Widgets（已有）
- 数据：AkShare（全市场免费）
- 回测：backtrader（多周期事件驱动）
- K线：ECharts + WebEngineView
- AI：akshare-one-mcp（MCP Server）
- 打包：PyInstaller

### 8个参考项目
- HQChart ⭐3293（K线图表算法）
- TuChart ⭐790（PyQt+ECharts集成）
- akshare-one-mcp ⭐145（MCP协议）
- ai-stock-dashboard ⭐67（AI量化）
- MultipleFactorRiskModel ⭐73（风控）
- stock-trading-bot-dashboard（A股+AKShare）
- order-book-simulator（撮合引擎）
- AlphaStock_A（数据+选股）

### 阶段计划（8阶段/约46小时）
阶段1-基础框架 → 阶段2-行情监控 → 阶段3-K线图表 → 阶段4-回测 → 阶段5-模拟交易 → 阶段6-风控 → 阶段7-AI集成 → 阶段8-打包发布

## 量化系统 Copaw 工作区（2026-04-09 全面更新）
- **工作区**：`C:\Users\chenz\.copaw\workspaces\quant-system\`

### 两套真实子系统
1. ****QuantDesk（自研完整系统）**：\F:\\量化封存\\量化系统\\QuantDesk\\   - 全自研：数据→信号→策略→风控→交易→复盘
   - **MCP Server**（FastMCP）：30+个工具
     - 行情：get_stock_quote / get_stock_kline / search_stock
     - AI分析：analyze_stock（综合评分/推荐/预测/支撑压力）/ scan_stocks / top_picks
     - 回测：run_backtest（backtrader：dual_ma/macd/rsi/boll）
     - 交易：buy/sell / get_account / get_positions / get_orders
     - 自动：get_auto_status / enable_auto_trade / run_daily_workflow
     - THS：connect_ths(SuperMind L2) / connect_ths_trader / ths_buy-sell
     - 复盘：get_hunan_replay（tgb.cn）/ get_daily_signal
   - 信号引擎：AI综合评分（趋势/均线/MACD/RSI/布林/预测概率）
   - 调度器：QuantScheduler（盘前/早盘/午盘/盘后）
   - 全自动引擎：auto_engine.py
   - ZeroMQ MessageBus + AllTick WS

2. **VNpy（框架+扩展）**：\F:\\量化封存\\量化系统\\VNpy\\   - REST API（端口9999）：账户/持仓/订单/K线/Tick
   - MCP Server（SSE:8101）：send_order / cancel_order / get_positions / get_account / run_backtest
   - OpenCode Wrapper：封装opencode-cli.exe供CoPaw调用
   - 策略包：dual_ma / mean_reversion / tick_strategy
   - 数据源：TDX通达信 → AkShare（自动切换）

### 关联系统
- **Strategies**：`F:\量化封存\量化系统\Strategies\`
  - 6个策略：AI打板/AI做T/Dual Thrust/London Breakout/Momentum Breakout/Supertrend Reversal
  - THS控制器：ths_controller.py（win32gui+SendInput）+ 12个调试脚本 + 20+张截图
- **ths_trade-main**：`F:\量化封存\量化系统\ths_trade-main\`
  - Tornado REST API（端口6003），支持70-80家券商
  - /api/queue（买卖）/api/search（查询持仓/成交/委托/资金）
- **stock_database**：`F:\量化封存\量化系统\stock_database\`
  - SQLite 2.2MB，10张表（新浪33字段/腾讯88字段/东财/akshare/mootdx/聚宽）
- **stock_database_full**：`F:\量化封存\量化系统\stock_database_full\`
  - SQLite 114KB，12张表（板块热度/行业/概念/逐笔/资金流）
- **QuantDesk_System**：`F:\量化封存\量化系统\QuantDesk_System\`（eFinance双服务参考版）
- **UnifiedEngine v3**：`F:\量化封存\量化系统\UnifiedEngine\`（QuantDesk+VNpy统一引擎）
- **tdx**：`F:\量化封存\量化系统\tdx\`（完整通达信安装目录）

### 两套子系统对比
| 维度 | QuantDesk（自研）| VNpy（框架）|
|------|-----------------|-------------|
| MCP工具 | 30+个 | 6个 |
| 数据 | AllTick WS + pytdx + AkShare | TDX + AkShare |
| 信号分析 | AI综合评分 + 湖南人复盘 | 无 |
| 全自动 | ✅ run_daily_workflow | ❌ |
| THS连接 | SuperMind L2 + xiadan | REST API |
| 调度器 | QuantScheduler | 需开发 |

### CoPaw 04/07-04/09 密集开发成果（90+ 脚本）
- **逐笔数据**：✅ `akshare.stock_zh_a_tick_tx_js`，002309实测4744笔/日
- **资金流**：✅ 120天历史（主力/大单/中单/小单/超大单）
- **AllTick**：✅ WebSocket A股/港股/美股（~170ms）
- **全量字段**：✅ 002309_数据字段清单.md（7KB）

### 最新Obsidian笔记
- **全面检查报告**：`已开发项目/量化系统/2026-04-09全面检查报告.md`（8KB，完整版）
- **功能架构笔记**：`已开发项目/量化系统/功能架构笔记.md`（30项全通过）
- **已开发项目笔记路径**：`C:\Users\chenz\Documents\Obsidian Vault\已开发项目\量化系统\`


## browser-control Skill（2026-04-12 新增）
| 编号 | 名称 | 路径 | 状态 |
|------|------|------|------|
| #22 | browser-control | workspace/skills/browser-control/ | ✅ 全面优化（20+原子操作/错误分类/自动重连/checkpoint）|
| #23 | windows-desktop-master | workspace/skills/windows-desktop-master/ | ✅ 已安装（12文件，38KB）— AutoHotkey+pywinauto+winremote-mcp |

## GitHub Skills 备份仓库（2026-04-07）

- **仓库**: https://github.com/SnowLove0303/openclaw-skills
- **本地路径**: `F:\工作区间\openclaw-skills`
- **技能数**: 16个（含 github-search/explorer 等免API技能）
- **自动同步**: Windows 计划任务 `OpenClawSkillsAutoSync`，每小时 09:00-23:00
- **同步脚本**: `F:\工作区间\openclaw-skills\.clawsync\sync.py`（Python版，已验证可用）
- **工作方式**: MD5 checksum 变更检测 + git add/commit/push

### 免API搜索技能
| 技能 | 数据源 | 说明 |
|------|--------|------|
| `github-search` | `gh search` | 仓库/代码/Issue搜索，认证CLI直接用 |
| `github-explorer` | `gh api` | 项目深度分析，自动采集README/Issues/Commits |

## SSH 环境（2026-04-13）
- **本机 IP**: `192.168.1.84`
- **SSH 专用账户**: `sshadmin` / `SshPass123!`
- **状态**: ✅ 已配置防火墙规则，可从局域网其他设备 SSH 连接
- **配置文件**: `C:\ProgramData\ssh\sshd_config`

---

## OpenClaw CLI Known Bug（2026-04-11）

**Bug #47133（已知）：** CLI WS 连接 Gateway 时，CLI 退出后 Gateway 收到 SIGTERM/SIGKILL 导致重启。
- 影响：所有 CLI 命令（`sessions list`/`cron list` 等）都会触发 Gateway 重启
- 复现：`openclaw sessions list` → Gateway SIGKILL
- 根因：CLI 通过 WebSocket 连接 Gateway，WS close 帧触发 Gateway 进程收到终止信号
- Issue: https://github.com/openclaw/openclaw/issues/47133
- 另见 #45750（WS 1000 close + handshake timeout）
- **已修复：** PR #47222 (commit 536dfdb) 在 2026.4.8+ 修复了这个问题
- **当前状态：** 用户版本 2026.4.7，建议升级到 2026.4.10
- **Workaround（不用升级）：**
  - Sessions: 通过 agent 内部 `sessions_list`/`sessions_spawn` 工具，不走 CLI
  - Gateway HTTP: `http://127.0.0.1:18789/health`（健康检查）
  - Cron jobs: 读 `C:\Users\chenz\.openclaw\cron\jobs.json`
  - 触发任务: 通过 agent 内部 cron 工具

## 待做

- [ ] 询问用户名字并更新 USER.md
- [ ] CoPaw API Key 配置(OPENAI_API_KEY / DASHSCOPE_API_KEY)
- [ ] CoPaw 飞书渠道接入
- [ ] ClawTeam 在 WSL2 中安装测试
- [ ] CrewAI 安装测试
- [ ] 安装 coding-agent CLI 工具
- [ ] 安装 gh CLI 并认证（网络不稳定，GitHub 直连超时）
- [ ] CoPaw 切换到 Kimi 模型（国内访问更稳定）
- [ ] 策略回测验证（用 backtesting.py 做历史回测）
- [ ] AI打板/做T - 需配置MINIMAX_API_KEY和FEISHU_WEBHOOK环境变量

## FunASR（2026-04-05 安装完成）
- **venv:** `F:\skill\funasr-skill\.venv`
- **Python:** `F:\skill\funasr-skill\.venv\Scripts\python.exe`
- **注意:** editdistance Cython 对 Python 3.13 不兼容，已用纯 Python 补丁替代（`editdistance.py` 在 site-packages）
- **运行测试:** `F:\skill\funasr-skill\.venv\Scripts\python.exe -c "import funasr; from funasr import AutoModel; print('OK')"`

## md_beautifier（2026-04-05）
- **路径:** `F:\openclaw1\.openclaw\workspace\skills\video-news-workflow\scripts\md_beautifier.py`
- **功能:** 中文间距、标点修正、YAML格式化、标题层级、空行压缩、列表统一
- **用法:** `python md_beautifier.py <file.md>` 或 `from md_beautifier import beautify`

## opencode-worker 测试 (2026-04-04)

## Omni-Search（2026-04-11 新增）
- **路径**: workspace/skills/omni-search/
- **定位**: 全渠道统一搜索入口，协调 search-layer + multi-engine + baidu + github
- **原理**: 意图路由 + 并行多源 + 统一去重排序

## 搜索类 Skills（2026-04-11 整合完毕）

| 编号 | 名称 | 功能 | 备注 |
|------|------|------|------|
| #2 | search-layer | Brave+Exa+Tavily+Grok 主协调层 | 已有，核心 |
| #22 | omni-search | 全渠道统一入口（新建） | 协调所有搜索渠道 |
| #23 | multi-search-engine | 17个搜索引擎 | curl 直接装 |
| #24 | multi-search-engine-simple | 10个国内搜索引擎精简版 | clawhub 装 |
| #25 | bailian-web-search | Bailian Web Search | clawhub 装 |
| #26 | baidu-search-1-1-0 | 百度搜索API版 | clawhub装，需BAIDU_API_KEY |
| #27 | agnxi-search-skill | AI工具/MCP目录搜索 | clawhub装 |
| #28 | search-bot | Brave实时搜索 | clawhub装，需AIPROX_TOKEN |

**Omni-Search 使用方式：**
- 通用搜索 → search-layer 协议执行（主通道）
- 中文/国内内容 → omni-search 自动并行 baidu + multi-engine
- GitHub 专项 → 已有 github-search/explorer（MEMORY记录）

## GitHub 专属工作空间（2026-04-11 新增）

- **仓库**: https://github.com/SnowLove0303/chunbi-workspace
- **路径**: F:\openclaw1\.openclaw\workspace\chunbi-workspace
- **用途**: 春笔的 AI 工作空间备份

### Skills 同步规则

- **同步脚本**: chunbi-workspace/sync_skills.py
- **同步目录**: skills/ 下每个 skill 单独一个文件夹
- **上传命令**: `python sync_skills.py`（在 chunbi-workspace 目录下）
- **跳过文件**: .pyc/.exe/.zip 等二进制，以及 > 5MB 的文件
- **已同步**: 23 个 skills，全部成功（0 失败）
- **本地路径**: F:\openclaw1\.openclaw\workspace\skills\

### ⚠️ 铁律：每次更新必须立即同步 GitHub

**规则**: 任何 skill 有代码/文档更新 → 必须当天同步到 chunbi-workspace

**操作流程**:
1. 修改 skill 文件（代码/SKILL.md/script/配置等）
2. `git add` + `git commit` + `git push` 到 chunbi-workspace
3. 如果 skill 文件多/大，用 `python sync_skills.py` 补充同步
4. 禁止本地积累未提交的 skill 更改过夜

**GitHub 仓库地址**:
- chunbi-workspace: https://github.com/SnowLove0303/chunbi-workspace

### 项目同步规则（2026-04-11 新增）

- **原则**: 有新开发项目时，自动在 chunbi-workspace 下创建子文件夹并同步上传
- **命名**: 每个项目单独一个文件夹，如 `projects/quant-system/`、`projects/obsidian-plugins/`
- **同步方式**: 把项目文件夹通过 Python 脚本或 gh api 上传到 GitHub
- **触发**: 项目有重要更新或阶段性成果时同步，避免代码丢失
- **示例**: 量化系统、Obsidian 插件开发、AI 工作流脚本等
