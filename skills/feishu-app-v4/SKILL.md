# 飞书应用创建自动化技能

## 技能概述

- **版本**: 4.0 整合版
- **触发关键词**: 飞书应用创建、创建飞书应用、飞书自动化、feishu app create
- **依赖**: Python 3.8+, Google Chrome, selenium (playwright/playwright 可选)
- **前置条件**: Chrome 已开启调试模式（--remote-debugging-port=9222）

## 核心能力

1. **自动登录态检测** - 复用已登录 Chrome 的飞书会话
2. **全自动创建应用** - 填写名称、描述、添加机器人能力
3. **权限批量导入** - 200+ 权限点一键导入（租户级 + 用户级）
4. **事件订阅配置** - 自动订阅 im.message.receive_v1 等事件
5. **凭证自动获取** - 提取 APP ID，提示保存 APP Secret
6. **版本发布** - 人工确认后发布

## 前置操作

### 1. 启动 Chrome 调试模式

```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\Users\$env:USERNAME\AppData\Local\Google\Chrome\User Data"
```

### 2. 登录飞书开发者后台

在 Chrome 中打开 https://open.feishu.cn/app，扫码登录。

### 3. 配置权限文件

在 `feishu_cdp_automation.py` 的 `CONFIG` 中设置 `permissions_file` 路径（JSON 格式）。

## 运行方式

```bash
cd skills/feishu-app-v4
pip install -r requirements.txt
python feishu_cdp_automation.py
```

或双击 `run.bat`。

## 配置项

| 字段 | 说明 | 默认值 |
|------|------|--------|
| `app_name` | 应用名称 | 飞书 Flow 测试 |
| `app_description` | 应用描述 | 1 |
| `permissions_file` | 权限 JSON 文件路径 | （需配置） |
| `debug_port` | Chrome 调试端口 | 9222 |
| `delay_range` | 人类延迟区间(秒) | (2, 5) |

## 输出产物

- `screenshots/` - 每步截图
- `logs/` - 执行日志
- 控制台输出 APP ID / APP Secret

## 技术架构

- 主协议：Chrome CDP（优先）
- 降级方案：Selenium CDP 模拟
- 选择器策略：CSS → XPath → text 三级降级
- 智能等待：waitForSelector + waitForFunction
