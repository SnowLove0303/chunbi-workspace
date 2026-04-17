---
name: tiao-bing-system-full
description: 调兵系统 - 统一控制 CoPaw / OpenClaw / OpenCode 三大 AI Agent 兵团。支持直接调用、web 界面快速打开、多兵团协作编排。
category: autonomous-ai-agents
---

# 调兵系统 (Tiao-Bing System)

统一控制 CoPaw / OpenClaw / OpenCode 三大 AI Agent 兵团。

## 一、核心接口脚本

| 脚本 | 路径 | 用途 |
|------|------|------|
| **统一调用** | `~/.hermes/scripts/tiao-bing-unified.py` | 通用入口 |
| **快捷 Shell** | `~/.hermes/scripts/tiao-bing-helpers.sh` | 简写命令 |
| **Open Web** | `~/.hermes/scripts/tiao-bing-open-web.py` | 快速打开 web |

---

## 二、快捷命令（推荐）

### 调用三兵团

```bash
# CoPaw（发散思考、角度拆解、风险提醒）
copaw "任务描述"
copaw "分析这个创意的风险点" --agent ep75k5

# OpenClaw（浏览器自动化、多步骤复杂任务）
openclaw "帮我登录飞书并发送消息"
openclaw "自动化操作" --agent codex-commander

# OpenCode（精确代码任务）
opencode "写一段 Python 快速排序"
```

### 打开 Web 界面

```bash
# 打开各系统 Web 界面
open-web copaw     # CoPaw 控制台
open-web openclaw  # OpenClaw 控制台
open-web opencode  # OpenCode Web UI
open-web all       # 全部打开
```

### 系统状态

```bash
tiao-status        # 查看三系统状态
```

### 列出可用 Agent

```bash
tiao-list copaw    # 列出 CoPaw agents
```

---

## 三、完整参数

### copaw

```bash
copaw <prompt> [--agent <id>] [--session <id>] [--timeout <秒>]
```

**可用 Agent:**
- `default` - 默认通用
- `ep75k5` - 整理仙人
- `CoPaw_QA_Agent_0.1beta1` - QA Agent
- `msUk59` - 量化专家
- `Unt9Ae` - OpenClaw 桥接
- `m65L7D` - OpenCode 桥接
- `UF5sMV` - 飞书管理

### openclaw

```bash
openclaw <prompt> [--agent <id>] [--session <alias>] [--timeout <秒>]
```

**可用 Agent:**
- `main` - 默认主 Agent
- `codex-commander` - 总指挥
- `codex-writer` - 写手
- `codex-reviewer` - 审核
- `xingzhengguan` - 行政官
- `codex-worker-1` - Worker

### opencode

```bash
opencode <prompt> [--timeout <秒>]
```

---

## 四、底层调用（绕过快捷命令）

### CoPaw HTTP API

```python
import urllib.request, json

payload = json.dumps({
    "session_id": "hermes-1",
    "input": [{"role": "user", "content": [{"type": "text", "text": "任务"}]}]
}).encode()

req = urllib.request.Request(
    "http://127.0.0.1:8088/api/agent/process",
    data=payload,
    headers={"X-Agent-Id": "default", "Content-Type": "application/json"},
    method="POST"
)
# 返回 SSE 流，需要解析
```

### OpenClaw Gateway

```bash
# 通过 PowerShell 调用 gateway-direct.mjs
powershell.exe -NoProfile -Command '
& "C:\Program Files\nodejs\node.exe" "F:\codex\codex\tools\openclaw-gateway-direct.mjs" ask --agent main --session test --timeout-sec 120 "任务"
'
```

### OpenCode CLI

```bash
"F:\AI\opencode\opencode-cli.exe" run "任务"
```

---

## 五、端口与地址

| 系统 | 地址 | 说明 |
|------|------|------|
| CoPaw API | `http://127.0.0.1:8088` | HTTP SSE |
| OpenClaw Gateway | `ws://127.0.0.1:18789` | WebSocket |
| OpenCode Web | `http://127.0.0.1:4096` | HTTP |

---

## 六、协作模式

### 单兵作战
```bash
copaw "发散思考这个创意"
openclaw "自动化网页操作"
opencode "写一段代码"
```

### 双兵协作
```bash
# Codex 风格：Plan → Execute → Review
# 1. CoPaw 发散
idea=$(copaw "拆解这个问题的多个角度")
# 2. OpenCode 执行
code=$(opencode "基于这些方向写代码")
# 3. OpenClaw 验证
result=$(openclaw "验证这段代码在浏览器中的表现")
```

---

## 七、文件结构

```
~/.hermes/scripts/
├── tiao-bing-unified.py   # 统一调用入口
├── tiao-bing-helpers.sh   # Shell 快捷命令
└── tiao-bing-open-web.py  # 快速打开 Web

~/.hermes/skills/tiao-bing-system-full/
├── SKILL.md               # 本文档
├── assistant-hub.ps1      # Windows 原生入口
├── orchestrate-helpers.ps1
├── openclaw-gateway-direct.mjs
---

## 八、坑点记录

### CoPaw SSE 流末尾空消息
CoPaw 返回的 SSE 流最后一个 `message completed` 事件往往是空的 `type=text`，需要取最后一个**非空** content：

```python
last_text = ""
for line in response:
    if '"type": "text"' in line:
        m = re.search(r'"text":\s*"([^"]*)"', line)
        if m:
            last_text = m.group(1)
# 返回 last_text，不要最后一个空消息
```

### OpenClaw WebSocket HMAC 认证无法在 Python 复现
OpenClaw 使用 HMAC-SHA256 challenge-response 认证，Python `websocket-client` 无法处理这种握手流程。**必须**通过 Node.js 脚本 `openclaw-gateway-direct.mjs` 调用：

```python
# 正确方式：PowerShell → Node.js
ps_script = f'& "C:\\\\Program Files\\\\nodejs\\\\node.exe" "F:\\\\codex\\\\codex\\\\tools\\\\openclaw-gateway-direct.mjs" ask --agent main --session {session} --timeout-sec 60 "{prompt}"'
result = subprocess.run(["/mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe", "-NoProfile", "-Command", ps_script], capture_output=True, text=True, timeout=timeout + 10)
```

**不要**尝试用 Python websocket-client 直接连 `ws://127.0.0.1:18789`。

### WSL 调用 Windows PowerShell 路径
在 WSL 里调用 PowerShell 必须用**完整路径**：

```python
# 正确
["/mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe", "-NoProfile", "-Command", script]

# 错误（找不到）
["powershell.exe", "-Command", script]
```

### OpenClaw Token 不需要手动传入
mjs 脚本会自动从 `F:\openclaw\openclaw.json` 读取 token，不需要作为参数传入。

### OpenClaw mjs 输出提取
mjs 脚本输出的是原始 JSON 文本，需要用正则提取：

```python
m = re.search(r'"output":\s*"([^"]*)"', raw_output)
content = m.group(1) if m else raw_output
```

### OpenClaw 配置 UTF-8 BOM
`openclaw.json` 文件有 UTF-8 BOM，读取时需指定：

```python
with open("/mnt/f/openclaw/openclaw.json", encoding="utf-8-sig") as f:
    config = json.load(f)
```

---

└── docs/
    ├── 调兵系统使用说明-2026-04-10.md
    ├── 调兵系统说明-2026-04-09.md
    └── 调兵系统完整报告-2026-04-07.md
```
