# windows-desktop-master Skill

> OpenClaw Windows 桌面精准控制终极方案 | 2026-04-13

---

## 技能定位

整合 AutoHotkey + pywinauto + winremote-mcp + OpenClaw 原生工具，覆盖：
- **宏录制回放**（AutoHotkey）
- **GUI 深度控制**（pywinauto）
- **40+ 系统工具**（winremote-mcp）
- **快速自动化**（OpenClaw windows-desktop__）

---

## 架构

```
用户任务
  │
  ▼
┌──────────────────────────────────────────────────────┐
│ Layer 1 · windows-desktop__ 工具（OpenClaw 内置）        │
│   Snapshot → Click/Move/Type → 完成                   │
└──────────────────────┬───────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────┐
│ Layer 2 · browser-control skill（Playwright）           │
│   浏览器 + SPA 页面控制                                │
└──────────────────────┬───────────────────────────────┘
                       ▼
┌──────────────────────────────────────────────────────┐
│ Layer 3 · windows-desktop-master                      │
│  ├─ AutoHotkey（宏录制/回放/编译exe）                   │
│  ├─ pywinauto（Windows GUI 深度控件控制）               │
│  └─ winremote-mcp（40+ 系统工具，MCP协议）              │
└──────────────────────────────────────────────────────┘
```

---

## 工具层说明

### Layer 1 · OpenClaw 原生工具

| 工具 | 用途 |
|------|------|
| `windows-desktop__Snapshot` | 截图 + UI 元素树 |
| `windows-desktop__Click` | 点击（坐标/标签）|
| `windows-desktop__Type` | 键盘输入 |
| `windows-desktop__Move` | 鼠标移动/拖拽 |
| `windows-desktop__Shortcut` | 组合键 |
| `windows-desktop__FileSystem` | 文件操作 |
| `windows-desktop__PowerShell` | PowerShell 命令 |
| `windows-desktop__Clipboard` | 剪贴板 |

### Layer 2 · AutoHotkey（需安装）

**安装**：运行 `F:\工作区间\ahk-install.exe`

| 功能 | 说明 |
|------|------|
| AHK 录制 | `scripts/ahk_recorder.py` 启动 AHK 内置 Recorder |
| AHK 执行 | `scripts/ahk_runner.py` 运行 .ahk 脚本 |
| AHK 编译 | 将 .ahk 编译为独立 .exe |

```python
# 示例：从 Python 执行 AHK 脚本
import subprocess
subprocess.Popen(['autohotkey.exe', 'F:\path\to\script.ahk'])
```

**常用 AHK 命令速查**：

| AHK 命令 | 等价 Windows 工具 | 说明 |
|----------|------------------|------|
| `Click, 100, 200` | `windows-desktop__Click` | 绝对坐标点击 |
| `Send, text` | `windows-desktop__Type` | 输入文本 |
| `Send, {Tab}` | `windows-desktop__Shortcut` | 按 Tab |
| `Sleep, 500` | `windows-desktop__Wait` | 等待 |
| `MouseMove, x, y` | `windows-desktop__Move` | 移动鼠标 |
| `Loop, 3 { ... }` | cron / loop | 循环重复 |

### Layer 3 · pywinauto

**安装**：`pip install pywinauto`（已有 v0.6.6）

| 核心功能 | 说明 |
|---------|------|
| 控件搜索 | `app.window(title_re='.*Notepad.*').child_window(title='Edit')` |
| 菜单操作 | `app.Notepad.menu_select('File -> Open')` |
| 窗口操作 | `app.window().minimize() / maximize() / close()` |
| 发送文本 | `edit.type_keys('Hello World')` |
| 按钮点击 | `button.click()` |

```python
# 基本用法
from pywinauto import Application

app = Application(backend='win32').start('notepad.exe')
app.Notepad.menu_select('Help -> About Notepad')
app.Notepad.Notepad['Edit'].type_keys('Hello', with_spaces=True)
```

**后端选择**：
- `win32`（默认）：Win32 API，适合标准 Windows 控件
- `uia`：UIAutomation，适合现代 Windows 10/11 应用

### Layer 4 · winremote-mcp

**安装**：`pip install winremote-mcp`（已有 v0.4.15）

40+ 工具覆盖：截图、剪贴板、进程、注册表、服务、WMI、网络、电源等。

详见：`references/winremote_mcp_tools.md`

---

## 脚本说明

| 脚本 | 用途 |
|------|------|
| `scripts/ahk_recorder.py` | 启动 AutoHotkey Recorder，生成 .ahk 文件 |
| `scripts/ahk_runner.py` | 在 OpenClaw 中执行 .ahk 脚本 |
| `scripts/pywinauto_helper.py` | pywinauto 常用封装（启动/点击/输入） |
| `scripts/winremote_check.py` | 检测 winremote-mcp 端口和工具状态 |
| `scripts/desktop_workflow.py` | 组合工作流入口（lobster step） |

---

## 依赖环境

```bash
pip install pywinauto winremote-mcp windows-mcp
# AutoHotkey: 运行 F:\工作区间\ahk-install.exe 安装
```

已验证版本：
- pywinauto: 0.6.6
- winremote-mcp: 0.4.15
- windows-mcp: 0.7.1
- AutoHotkey: v2.0（安装后可用）

---

## 快速开始

### 1. 录制宏（AutoHotkey）

```bash
python scripts/ahk_recorder.py --output "F:\工作区间\my_macro.ahk"
# 弹出 AHK Recorder，按 Ctrl+Shift+R 开始录制，Ctrl+Shift+R 停止
# 脚本自动保存到 --output 指定路径
```

### 2. 执行 AHK 宏

```bash
python scripts/ahk_runner.py "F:\工作区间\my_macro.ahk"
```

### 3. pywinauto 控制桌面应用

```python
from pywinauto_helper import AppController

ctl = AppController(backend='win32')
ctl.launch('E:/ths/同花顺/hexin.exe')
ctl.wait_window(title_re='.*同花顺.*', timeout=10)
ctl.click_button('下单')  # 按文本或控件名
ctl.type_into('Edit', '000001')
ctl.press('Tab')
```

### 4. 组合工作流

```bash
python scripts/desktop_workflow.py --workflow "examples/auto_trade.yaml"
```

---

## 常见场景

### 场景 1：THS 同花顺下单（已有方案）

使用 `ths_controller.py`（THS 专属控件控制）已验证。

参考：`C:\Users\chenz\Documents\Obsidian Vault\开发项目ing\量化\THS控制器.md`

### 场景 2：自动填表

```
Snapshot（windows-desktop）→ 读取坐标 → AHK 或 pywinauto 填入
```

### 场景 3：定时重复操作

```
录制 AHK 宏 → 定时 exec 执行（cron） → 编译成 .exe 脱离环境运行
```

---

## 故障排查

| 问题 | 排查 |
|------|------|
| AHK 脚本不运行 | 确认已安装 AutoHotkey，`autohotkey.exe` 在 PATH |
| pywinauto 找不到控件 | 尝试切换 `backend='uia'`，用 `print_control_identifiers()` 调试 |
| winremote-mcp 无响应 | `python scripts/winremote_check.py` 检测 MCP 端口 |
| 坐标点击不准 | 用 `windows-desktop__Snapshot` 确认元素坐标 |
| 权限不足 | 右键 "以管理员身份运行" OpenClaw |
