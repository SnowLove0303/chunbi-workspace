# windows-desktop-master

> OpenClaw Windows 桌面精准控制终极方案 | 2026-04-13

## 能力概览

整合四大工具层，覆盖所有 Windows 桌面自动化场景：

| 工具层 | 组件 | 能力 |
|--------|------|------|
| **Layer 1** | OpenClaw `windows-desktop__` | 截图、点击、文件、进程等 18 个内置工具 |
| **Layer 2** | browser-control skill | Playwright 浏览器 + SPA 页面 |
| **Layer 3** | AutoHotkey | 宏录制/回放/编译 exe |
| **Layer 3** | pywinauto | Windows GUI 深度控件控制 |
| **Layer 3** | winremote-mcp | 40+ 系统工具（MCP 协议）|

## 安装

```bash
# 1. AutoHotkey（宏录制）
运行 F:\工作区间\ahk-install.exe

# 2. Python 依赖
pip install pywinauto winremote-mcp windows-mcp
```

## 快速开始

### 录制 AHK 宏

```bash
python scripts/ahk_recorder.py --output "F:\工作区间\my_macro.ahk"
# 按 Ctrl+Shift+R 开始/停止录制
```

### 执行 AHK 宏

```bash
python scripts/ahk_runner.py "F:\工作区间\my_macro.ahk"
```

### pywinauto 控制桌面应用

```python
from scripts.pywinauto_helper import AppController

ctl = AppController(backend='win32')
ctl.launch(r'E:\ths\同花顺\hexin.exe')
ctl.wait_window(title_re='.*同花顺.*', timeout=10)
ctl.click_button('下单')
ctl.type_into('Edit', '000001')
```

### Desktop Workflow

```bash
python scripts/desktop_workflow.py --action run --workflow "examples/ths_auto_trade.yaml"
```

## 文件结构

```
windows-desktop-master/
├── SKILL.md                          # 技能说明文档
├── README.md                          # 本文件
├── skill.json                         # Skill 元数据
├── scripts/
│   ├── ahk_recorder.py               # AHK 录制器
│   ├── ahk_runner.py                  # AHK 执行器
│   ├── pywinauto_helper.py           # pywinauto 封装
│   ├── winremote_check.py            # MCP 状态检测
│   └── desktop_workflow.py           # lobster step 入口
├── references/
│   ├── winremote_mcp_tools.md        # 40+ 工具清单
│   └── ahk_quickref.md               # AHK v2 速查
└── examples/
    ├── ths下单流程.ahk               # THS 下单宏
    └── ths_auto_trade.yaml           # 下单 Workflow
```

## 与现有 skills 的关系

| Skill | 定位 |
|-------|------|
| `browser-control` | 浏览器 + 有结构页面 |
| **`windows-desktop-master`** | **Windows 原生桌面 + 宏录制** |
| `adb` | Android 设备控制 |

## GitHub

- 同步仓库: https://github.com/SnowLove0303/openclaw-skills
- 本地路径: F:\openclaw1\.openclaw\workspace\skills\windows-desktop-master
