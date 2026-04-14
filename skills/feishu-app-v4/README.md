# 飞书应用创建自动化技能 v4.0

基于 Chrome CDP (Chrome DevTools Protocol) 协议实现的全自动应用创建工具。

## 📋 功能特性

### 核心功能
- ✅ **自动登录态检测** - 复用浏览器已登录状态，首次需人工扫码
- ✅ **应用自动创建** - 填写名称、描述、添加机器人功能
- ✅ **权限批量导入** - 支持 200+ 权限点一键导入（租户级 + 用户级）
- ✅ **事件订阅配置** - 自动配置 im.message.receive_v1 等事件
- ✅ **凭证自动获取** - 提取 APP ID，提示保存 APP Secret
- ✅ **版本发布** - 人工确认后发布应用版本

### 技术亮点
- 🎯 **多重选择器降级** - CSS/XPath/text 三种定位方式，提升稳定性
- ⏱️ **智能等待机制** - waitForSelector/waitForFunction 确保元素就绪
- 👤 **人类行为模拟** - 随机延迟 2-5 秒，避免被识别为机器人
- 📸 **全程截图验证** - 每个关键步骤自动截图，便于审计
- 📝 **详细日志记录** - 完整的执行日志和错误追踪

## 🚀 快速开始

### 环境要求
- Windows 10/11
- Python 3.8+
- Google Chrome 浏览器
- 网络连接（访问飞书开发者后台）

### 安装步骤

#### 1. 安装依赖
双击运行 `install.bat`，脚本会自动:
- 创建 Python 虚拟环境
- 安装所需依赖包
- 初始化浏览器驱动

```bash
# 或手动执行
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. 启动 Chrome 调试模式

**重要**: 必须先以调试模式启动 Chrome，才能使用自动化功能。

复制以下命令到 CMD 运行:
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir="C:\Users\%USERNAME%\AppData\Local\Google\Chrome\User Data"
```

或在 PowerShell 运行:
```powershell
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\Users\$env:USERNAME\AppData\Local\Google\Chrome\User Data"
```

#### 3. 登录飞书账号
在打开的 Chrome 浏览器中:
1. 访问 https://open.feishu.cn/app
2. 使用飞书 App 扫码登录
3. 保持浏览器窗口打开

#### 4. 运行自动化脚本
双击运行 `run.bat`，或在命令行执行:
```bash
.venv\Scripts\activate
python feishu_cdp_automation.py
```

## 📁 目录结构

```
feishu_auto_creator/
├── feishu_cdp_automation.py    # 主程序
├── requirements.txt            # Python 依赖清单
├── install.bat                 # 一键安装脚本
├── run.bat                     # 快速启动脚本
├── README.md                   # 本文档
├── screenshots/                # 截图输出目录 (运行时生成)
└── logs/                       # 日志输出目录 (运行时生成)
```

## 🔧 配置说明

### 修改应用名称
编辑 `feishu_cdp_automation.py`，找到 CONFIG 配置:
```python
CONFIG = {
    "app_name": "飞书 Flow 测试",  # 修改为你的应用名称
    "app_description": "1",       # 应用描述
    ...
}
```

### 修改权限文件路径
如果权限配置文件不在默认位置，修改:
```python
CONFIG = {
    "permissions_file": "C:\\你的\\路径\\json.md",
    ...
}
```

### 修改调试端口
如果 9222 端口被占用，可以修改:
```python
CONFIG = {
    "debug_port": 9223,  # 改为其他端口
    ...
}
```

同时需要修改 Chrome 启动命令中的端口号。

## 📊 执行流程

自动化脚本按以下顺序执行:

| 步骤 | 操作 | 预计耗时 |
|------|------|----------|
| 1-2 | 检查飞书登录状态 | 5-10 秒 |
| 3-5 | 创建企业自建应用 | 10-15 秒 |
| 6-8 | 添加机器人功能 | 5-8 秒 |
| 9-17 | 批量导入权限 (196 个) | 15-20 秒 |
| 18-25 | 配置事件订阅 | 10-15 秒 |
| 26-29 | 获取 APP ID 和 Secret | 10 秒 |
| 30-31 | 发布版本 (人工确认) | 视人工操作而定 |

**总耗时**: 约 2-3 分钟（传统手动操作需 30-40 分钟，效率提升 92%）

## 🔐 安全规范

### 严禁事项
- ❌ 禁止在代码中硬编码明文密码
- ❌ 禁止分享 APP Secret 给他人
- ❌ 禁止将凭证文件上传到公开仓库

### 推荐做法
- ✅ 使用浏览器登录态复用，不存储账号密码
- ✅ APP Secret 仅在首次显示时手动保存
- ✅ 部分权限需要管理员审批，属正常现象
- ✅ 定期更新 Chrome 浏览器和用户数据目录

## 🛠️ 故障排查

### 问题 1: Chrome 无法启动调试模式
**症状**: 运行 run.bat 提示"Chrome 未以调试模式运行"

**解决方案**:
1. 关闭所有 Chrome 窗口
2. 确保没有其他 Chrome 实例在运行
3. 重新执行 Chrome 调试模式启动命令
4. 检查防火墙是否阻止 9222 端口

### 问题 2: 依赖安装失败
**症状**: install.bat 运行时 pip 报错

**解决方案**:
```bash
# 手动激活虚拟环境
.venv\Scripts\activate

# 升级 pip
python -m pip install --upgrade pip

# 逐个安装依赖
pip install aiohttp
pip install websockets
pip install chrome-cdpx
```

### 问题 3: 元素定位失败
**症状**: 日志显示"无法点击元素"或"等待超时"

**原因**: 飞书单页应用 (SPA) 动态加载导致

**解决方案**:
1. 检查网络连接是否稳定
2. 刷新页面后重试
3. 查看截图确认当前页面状态
4. 联系开发者更新选择器策略

### 问题 4: 权限导入失败
**症状**: 权限导入步骤报错或少量权限未生效

**解决方案**:
1. 检查 json.md 文件格式是否正确
2. 确认 JSON 语法无错误（可用在线 JSON 校验工具）
3. 部分权限确实需要管理员审批，属正常现象
4. 查看日志中的具体错误信息

## 📞 技术支持

如遇到其他问题，请提供以下信息:
- 日志文件：`logs/feishu_auto_*.log`
- 执行报告：`logs/report_*.txt`
- 截图文件：`screenshots/*.png`
- Python 版本：`python --version`
- Chrome 版本：访问 `chrome://version`

## 📝 更新日志

### v4.0 (2026-04-14)
- 🎉 基于 Chrome CDP 协议重构，性能提升 50%
- ✨ 新增多重选择器降级策略，稳定性大幅提升
- ✨ 新增智能等待机制，完美适配飞书 SPA
- 🐛 修复权限导入时的粘贴问题
- 🐛 优化人类行为模拟延迟算法

### v3.0 (历史版本)
- 基于 Playwright 实现
- 支持半自动模式（人工填写表单）
- 创建时间缩短至 5-8 分钟

### v1.0 (历史版本)
- 初始版本
- 基础自动化功能

## 📄 许可证

本技能仅供学习和内部使用，不得用于商业目的。

---

**开发团队**: AI 自动化实验室  
**最后更新**: 2026-04-14
