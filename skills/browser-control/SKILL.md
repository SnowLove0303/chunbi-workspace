---
name: browser-control
description: 浏览器自动化控制框架。使用场景：(1) 构建浏览器自动化工作流 (2) 网页数据抓取/采集 (3) AI 浏览器 Agent 开发 (4) Playwright MCP / lobster Workflow 开发 (5) 浏览器控制脚本开发。触发条件：用户提到浏览器自动化、Playwright、browser-use、stagehand、lobster Workflow、浏览器工作流、网页监控、自动化测试等相关需求。
---

# 浏览器自动化控制框架

## 真实执行路径（三条路）

| 路径 | 工具 | 何时用 | 配置方式 |
|------|------|--------|---------|
| **路径A** | `browser` 工具（OpenClaw 内置） | 对话中直接控制浏览器 | 已启用，直接用 |
| **路径B** | fast-playwright-mcp（MCP 服务器） | AI Agent 需要 MCP 协议交互 | 已配置到 OpenClaw MCP |
| **路径C** | browser_control Python 包 + lobster | 复杂流水线、交互式操作 | `browser_control/` 包直接调用 |

---

## 路径A：browser 工具（对话级，直接用）

OpenClaw 内置，无需任何配置。对话中直接使用：
```
browser action=screenshot
browser action=navigate url=https://...
browser action=act selector=#kw kind=click
browser action=act selector=#kw kind=type text=Hello
```

---

## 路径B：fast-playwright-mcp（AI Agent 交互）

**已安装并配置到 OpenClaw MCP：**
- `browser_navigate` / `browser_click` / `browser_type`
- `browser_screenshot` / `browser_evaluate`
- `browser_batch_execute` — 多步合一，节省 token

**Token 节省参数（已在 MCP 配置中默认关闭）：**
- `includeSnapshot: false` / `includeCode: false` / `includeConsole: false`

---

## 路径C：browser_control Python 包 + lobster Workflow（⭐交互式开发核心）

这是本 skill 的交互式自动化开发体系，支持完整的 DOM 操作（click/type/scroll/extract）。

### 架构概览

```
lobster Workflow YAML（编排层）
  └─ python lobster_steps.py --action run_workflow
        └─ browser_control/client.py（执行层）
              └─ playwright.sync_api → CDP 端口 9222（浏览器层）
```

### 核心包：browser_control/

```
browser_control/
├── client.py          # BrowserClient（连接 Chrome CDP）+ run_actions()
│                        支持: 自动重连 / ud__ 选择器 / 20+ 原子操作
├── actions.py         # 动作工厂函数（nav/click/type/extract/...）
├── lobster_steps.py   # lobster workflow step CLI（独立可调用的 step）
├── retry.py           # 重试装饰器 + 错误分类（BrowserStepError 体系）
└── examples/
    ├── baidu_search.json         # 百度搜索示例
    └── browser-interactive-workflow.yaml  # lobster workflow 模板
```

### 可用原子操作

| action | 参数 | 说明 |
|--------|------|------|
| `nav` | `url`, `wait_until` | 导航到 URL |
| `click` | `selector`, `force`, `delay` | 点击元素（force=True 绕过可见性） |
| `type` | `selector`, `text`, `clear` | 输入文本（先 Ctrl+A 清空） |
| `press` | `key`, `selector` | 按键（Enter/Tab/Escape 等） |
| `wait_selector` | `selector`, `state` | 等待元素出现 |
| `wait_timeout` | `ms` | 固定等待 |
| `extract` | `selector`, `attr`, `text`, `all_`, `as` | 提取文本/属性/全部 |
| `extract_table` | `selector`, `as` | 提取表格为字典列表 |
| `screenshot` | `path`, `full_page`, `selector` | 截图 |
| `scroll` | `to`, `selector`, `delta_y` | 滚动（top/bottom/坐标） |
| `scroll_until_load` | `selector`, `delta_y` | 懒加载滚动（自动翻页） |
| `eval_js` | `script` | 执行 JavaScript |
| `extract_all` | `selector`, `schema` | 批量提取多条记录（schema 映射） |
| `get_cookies` | - | 获取当前 cookies |
| `set_cookies` | `cookies` | 恢复登录态 |
| `html` | `selector` | 提取 HTML |
| `select` | `selector`, `value` | 下拉框选择 |
| `hover` | `selector` | 悬停 |
| `rightclick` | `selector` | 右键菜单 |
| `hotkey` | `keys` | 组合键（Control+c 等） |
| `wait_url` | `pattern` | 等待 URL 匹配 |
| `fill` | `selector`, `text` | React 受控组件专用（直接 set value） |

---

### 开发流程（4 步）

#### 第 1 步：用 browser 工具手动调试

在对话中直接调试，找到正确的 selector 和操作序列：
```
browser action=snapshot targetUrl=https://www.baidu.com
# 找到搜索框 selector: #kw
browser action=act selector=#kw kind=type text=Python
browser action=act selector=#su kind=click
browser action=screenshot
```

#### 第 2 步：把动作序列写成 JSON 文件

把调试好的步骤转成 JSON workflow 文件：

```json
[
  {"action": "nav", "url": "https://www.baidu.com"},
  {"action": "wait_timeout", "ms": 2000},
  {"action": "eval_js", "script": "document.querySelector('#kw').value = 'Python'"},
  {"action": "press", "key": "Enter"},
  {"action": "wait_timeout", "ms": 2500},
  {"action": "screenshot", "path": "screenshots/baidu_search.png", "full_page": true},
  {"action": "extract", "selector": ".c-container", "text": true, "all_": true, "as": "search_results"}
]
```

保存到 `browser_control/examples/your_workflow.json`

#### 第 3 步：注册为 lobster workflow step

写一个 lobster YAML 来编排这个 JSON workflow：

```yaml
name: my-interactive-workflow
variables:
  workflow_file:
    default: "examples/your_workflow.json"
  chrome_port:
    default: "9222"

steps:
  - id: pre-check-chrome
    run: curl -s --connect-timeout 3 http://127.0.0.1:${chrome_port}/json/version > nul && echo OK || echo FAIL
    on_error: abort

  - id: run-interactive-workflow
    run: python browser_control/lobster_steps.py --action run_workflow --workflow ${workflow_file} --cdp-url http://127.0.0.1:${chrome_port}
    timeout: 120000

  - id: verify
    run: python -c "import json,os; p='output/workflow_result.json'; print('PASS' if os.path.exists(p) else 'FAIL')"
    on_error: continue
```

#### 第 4 步：执行 + checkpoint 审批

```bash
# 单次执行
python browser_control/lobster_steps.py --action run_workflow --workflow examples/your_workflow.json --cdp-url http://127.0.0.1:9222

# lobster workflow 编排（带 checkpoint）
lobster run browser_control/examples/browser-interactive-workflow.yaml --args-json '{"workflow_file":"examples/your_workflow.json"}' --mode tool
```

---

### lob

ster_steps.py CLI（直接用）

```bash
# 单步操作
python browser_control/lobster_steps.py --action navigate --url "https://example.com" --cdp-url http://127.0.0.1:9222
python browser_control/lobster_steps.py --action click --selector "#submit" --cdp-url http://127.0.0.1:9222
python browser_control/lobster_steps.py --action type --selector "#kw" --text "Hello" --cdp-url http://127.0.0.1:9222
python browser_control/lobster_steps.py --action screenshot --path "screenshots/page.png" --cdp-url http://127.0.0.1:9222
python browser_control/lobster_steps.py --action extract --selector "h1" --as-key "title" --cdp-url http://127.0.0.1:9222

# 执行 JSON workflow
python browser_control/lobster_steps.py --action run_workflow --workflow examples/baidu_search.json --cdp-url http://127.0.0.1:9222

# 交互式调试（从 stdin 逐条输入动作）
python browser_control/lobster_steps.py --action interactive --cdp-url http://127.0.0.1:9222
```

---

### 验证工具

#### 三维验证器（verify_step.py）

```bash
# 功能精准度
python scripts/verify_step.py --step check_nav \
  --expected-url "baidu.com" --actual-url "https://baidu.com" \
  --selector "#kw" --expected-state matched --actual-state matched

# 效率得分
python scripts/verify_step.py --step check_perf \
  --timeout-ms 5000 --actual-time-ms 2100

# 成果达标率
python scripts/verify_step.py --step check_output \
  --file-path "output/workflow_result.json" \
  --required-fields "url,screenshot,steps"

# 综合判定（最终调用）
python scripts/verify_step.py --step check_all
```

评分标准：
- `PASS` = 所有维度 >= 60
- `RETRY` = 部分维度 < 60，无维度 < 40
- `ABORT` = 任何维度 < 40
- `PASS*` = 无验证数据（降级通过）

#### Checkpoint 系统（checkpoint.py）

```bash
# 保存当前登录态
python scripts/checkpoint.py --action save --name "logged_in"

# 列出所有 checkpoint
python scripts/checkpoint.py --action list

# 验证 checkpoint
python scripts/checkpoint.py --action verify --name "logged_in" \
  --verify-url "app.example.com/dashboard"

# 对比两个 checkpoint
python scripts/checkpoint.py --action diff --name "step1.json" --other "step2.json"

# 恢复登录态
python scripts/checkpoint.py --action restore --name "logged_in"
```

#### 一键运行器（run_browser_workflow.py）

```bash
# 自动 Chrome + lobster workflow
python scripts/run_browser_workflow.py --target "https://example.com"

# 列出可用引擎
python scripts/run_browser_workflow.py --list-engines

# lobster 失败自动回退到 Playwright CLI
python scripts/run_browser_workflow.py --target "..." --engine auto

# lobster dry-run
python scripts/run_browser_workflow.py --target "..." --engine lobster --dry-run
```

### 错误分类与自动重连

`client.py` 内置自动重连 + 错误分类：

| 错误类型 | 说明 | 重试 |
|---------|------|------|
| `SELECTOR_NOT_FOUND` | 选择器未命中 | ✓ |
| `TIMEOUT` | 操作超时 | ✓ |
| `BROWSER_DISCONNECTED` | 浏览器断开 | ✓（自动重连）|
| `NAVIGATION_ERROR` | DNS/拒绝连接 | ✓ |
| `NETWORK_ERROR` | 网络错误 | ✓ |
| 其他 | 未知错误 | ✗（直接抛出）|

`ud__` 选择器简写（自动转换为 `[class*=xxx]`）：
```json
{"action": "click", "selector": "ud__dialog__root >> ud__dialog__content >> button"}
```
→ `[class*=dialog-root] [class*=dialog-content] button`

---

### 常见问题处理

**Q: 元素被 overlay 遮挡，无法点击？**
```json
{"action": "eval_js", "script": "document.querySelector('#kw').value = 'text'"}
```
用 `eval_js` 直接操作 DOM 绕过 overlay。

**Q: 元素是 hidden，无法交互？**
```json
{"action": "click", "selector": "#kw", "force": true}
```
`force=True` 绕过 actionability 检查。

**Q: 页面是 SPA，元素动态加载？**
```json
{"action": "wait_selector", "selector": "#content", "state": "visible", "timeout": 15000}
```
等待元素出现后再继续。

**Q: 表格数据跨页？**
在 JSON workflow 里加多步：第 1 页提取 → 点击"下一页"按钮 → 第 2 页提取 → ...

---

## 执行前端口检测（必须）

```bash
python scripts/check_ports.py
```

**检测逻辑：**
- Chrome CDP 9222 → 有则复用（保留登录态）/ 无则自动启动
- OpenClaw Gateway 18789 → 确认在线

---

## lobster Workflow（OpenClaw Agent 工具）

lobster 是 OpenClaw 插件工具，当 AI Agent 判定需要编排多步骤工作流时，通过 agent 内部调用。lobster workflow YAML 支持：
- `variables:` 定义可替换变量
- `steps:` 顺序执行，每步可独立失败处理
- `on_error: abort/continue` 错误控制
- `always_run: true` 清理/保存总是执行
- `timeout:` 步骤超时

---

## 三维验证（每个关键步骤后必须）

| 维度 | 及格线 | 检查内容 |
|------|--------|---------|
| 功能精准度 | ≥ 60 | selector 命中 / DOM 状态 / URL 跳转 |
| 效率得分 | ≥ 60 | 导航<5s / 点击<2s / 提取<3s |
| 成果达标率 | ≥ 60 | JSON 字段完整 / 截图可辨识 |

---

## 目录结构

```
browser-control/
├── SKILL.md                      ← 你在这里
├── browser_control/
│   ├── __init__.py               # 包入口
│   ├── client.py                 # BrowserClient + run_actions()
│   ├── actions.py                # 动作工厂（nav/click/type/extract/...）
│   ├── lobster_steps.py           # lobster step CLI 入口
│   └── examples/
│       ├── baidu_search.json             # 百度搜索示例（7步）
│       └── browser-interactive-workflow.yaml  # lobster workflow 模板
├── scripts/
│   ├── check_ports.py            # 端口检测
│   ├── verify_step.py            # 三维验证器
│   ├── checkpoint.py             # Checkpoint 持久化
│   ├── run_browser_workflow.py   # Playwright CLI 工作流
│   ├── run_lobster_workflow.py   # lobster workflow 执行器
│   └── save_result.py            # 结果保存
└── references/
    ├── main-doc.md
    ├── tools-detail.md
    └── workflow-guide.md
```

---

## 开发原则

1. **先 browser 工具调试**：找到正确的 selector 和操作序列，再写 JSON
2. **先端口检测**：Chrome 9222 没起来，一切免谈
3. **交互类操作用路径C**：nav → click → type → extract → screenshot 完整链路
4. **固定流水线用 lobster**：多步骤、带变量传递、checkpoint 审批
