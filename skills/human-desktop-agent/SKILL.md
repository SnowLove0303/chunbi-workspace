---
name: human-desktop-agent
description: |
  真人级桌面 Agent：browser-use + 屏幕解析双引擎。
  用途：(1) AI 操控浏览器完成网页任务 (2) 截屏理解界面 (3) 自然语言控制桌面操作。
  触发词：浏览器自动化、网页操作、屏幕理解、桌面控制、真人接管。
triggers:
  - browser-use
  - 浏览器自动化
  - 屏幕解析
  - 桌面控制
  - 真人接管
  - 网页任务
---

# Human Desktop Agent ✒️

browser-use + 屏幕解析双引擎，实现真人级桌面控制。

## 架构

```
用户任务
   │
   ├── 模式1: 浏览器自动化
   │      └─→ browser-use + MiniMax M2.7
   │             └─→ 自动操作 Chrome
   │
   └── 模式2: 屏幕理解 + 桌面控制
          └─→ 截图 → MiniMax 视觉理解 → pyautogui 执行
```

## 核心模块

### 1. BrowserAgent - 浏览器自动化
基于 browser-use，支持 MiniMax/GPT/Claude 等 LLM

```python
from lib.browser_agent import BrowserAgent
import asyncio

async def main():
    agent = BrowserAgent()
    result = await agent.run("打开百度并搜索 AI")
    print(result)

asyncio.run(main())
```

### 2. ScreenParser - 屏幕解析
截图 + MiniMax 视觉理解

```python
from lib.screen_parser import ScreenParser

parser = ScreenParser()
path = parser.capture_screen()
desc = parser.describe_screen(path, "找出所有可点击按钮")
```

### 3. DesktopAutomation - 基础桌面控制
pyautogui + pygetwindow

```python
from lib.desktop_automation import click, screenshot, list_windows

# 截图
screenshot("C:/temp/screen.png")

# 点击
click(100, 200)

# 列出窗口
windows = list_windows()
```

## CLI 用法

```bash
# 浏览器任务
python scripts/human_desktop.py "打开百度并搜索 AI"

# 屏幕理解
python scripts/human_desktop.py --screen "描述这个界面"

# 演示模式
python scripts/human_desktop.py --demo
```

## 配置

### 环境变量（已配置）
```bash
OPENROUTER_API_KEY=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
MINIMAX_API_KEY=sk-cp-VmUpM6ECqaSgr33MzjKMQNgy8cFgArOp0CHifxdVi7qsjPUva3I-dmyTkqPreAyS53oSQZzZyCFFLP-bTbgfIXCnaqc7Iv2TJQgsE3fY5ntSxeddnX-XH_o
```

### 浏览器配置
```python
from lib.browser_agent import BrowserConfig, BrowserAgent

config = BrowserConfig(
    headless=False,           # 是否无头模式
    cdp_url="ws://localhost:9222",  # 复用已打开的 Chrome
    chrome_path="C:/Program Files/Google/Chrome/Application/chrome.exe"
)
agent = BrowserAgent(config)
```

## 依赖

| 包 | 用途 | 状态 |
|----|------|------|
| browser-use | 浏览器自动化 | ✅ 已安装 |
| pyautogui | 鼠标/键盘控制 | ✅ 已安装 |
| pygetwindow | 窗口管理 | ✅ 已安装 |
| Pillow | 图像处理 | ✅ 已安装 |
| opencv-python | 图像识别 | ✅ 已安装 |

## 示例任务

### 浏览器自动化
```python
# 打开网页并操作
await agent.run("登录 GitHub")
await agent.run("在淘宝搜索 iPhone 15")
await agent.run("填写并提交这个表单")
```

### 屏幕控制
```python
# 截屏理解
parser = ScreenParser()
parser.capture_screen()
parser.describe_screen(path, "点击开始按钮")

# 图像识别点击
from lib.desktop_automation import find_image_on_screen, click
pos = find_image_on_screen("start_button.png")
if pos:
    click(pos[0], pos[1])
```

## 工作流程

1. **browser-use** 负责 AI 驱动的浏览器控制
   - AI 理解网页结构
   - 自动生成操作序列
   - 执行点击/输入/滚动

2. **ScreenParser** 负责屏幕理解
   - 截图当前界面
   - MiniMax 视觉分析
   - 提取可交互元素

3. **DesktopAutomation** 负责底层控制
   - 鼠标/键盘事件
   - 窗口管理
   - 图像匹配

## 安全说明

⚠️ 此 Skill 会控制浏览器和桌面操作：
- 敏感操作（登录/支付）请谨慎
- 建议先在测试环境验证
- AI 理解可能不准确，建议重要操作前确认

## 文件结构

```
human-desktop-agent/
├── SKILL.md
├── skill.json
├── lib/
│   ├── __init__.py
│   ├── browser_agent.py      # 浏览器自动化
│   ├── screen_parser.py      # 屏幕解析
│   ├── desktop_automation.py # 基础桌面控制
│   └── unified_agent.py      # 统一入口
└── scripts/
    ├── run_browser_task.py   # 浏览器任务脚本
    ├── demo.py               # 演示脚本
    └── human_desktop.py      # 统一入口
```

## 参考

- browser-use: https://github.com/browser-use/browser-use
- OmniParser: https://github.com/microsoft/OmniParser
- pyautogui: https://pyautogui.readthedocs.io/
