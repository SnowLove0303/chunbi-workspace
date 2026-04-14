# 1688 选品 + 拼多多运营自动化技能

> 全自动电商运营解决方案 - 智能选品、一键上架、订单处理、库存同步、数据报表

## 📋 功能特性

### 核心功能

| 模块 | 功能描述 | 状态 |
|------|---------|------|
| **1688 智能选品** | 自动采集热销商品、利润测算、供应商评估、风险检测 | ✅ |
| **拼多多商品上架** | 标题优化、一键发布、多店铺管理、SKU 定价 | ✅ |
| **订单自动处理** | 订单监控、自动确认、采购单生成、异常处理 | ✅ |
| **库存同步管理** | 供应商库存监控、自动同步、低库存预警 | ✅ |
| **数据报表生成** | 销售日报/周报/月报、商品排行、利润分析 | ✅ |
| **合规检测** | 违禁词检测、广告法检查、品牌侵权风险 | ✅ |

### 技术特点

- 🔄 **混合模式**：优先 API 对接，降级为浏览器自动化
- 🏪 **多店铺支持**：轻松管理多个拼多多店铺
- 🔐 **反检测机制**：内置反爬虫策略，降低封号风险
- 📊 **数据可视化**：Excel 报表自动生成和推送
- ⏰ **定时任务**：支持 Cron 表达式配置自动化任务
- 💬 **钉钉通知**：关键事件实时推送

---

## 🚀 快速开始

### 环境要求

- **操作系统**: Windows 10/11
- **Python**: 3.10 或更高版本
- **浏览器**: Microsoft Edge 或 Google Chrome（最新版）

### 安装步骤

#### 1. 安装 Python 依赖

```bash
cd ecommerce_skill
pip install -r requirements.txt
```

#### 2. 安装 Playwright 浏览器

```bash
playwright install edge
# 或
playwright install chrome
```

#### 3. 配置参数

编辑 `config.yaml` 文件，修改以下配置：

```yaml
# 1688 选品关键词
source_1688:
  selection:
    keywords:
      - "居家日用"
      - "收纳整理"
      - "厨房用品"

# 拼多多店铺信息
platform_pdd:
  shops:
    - shop_id: "shop_001"
      shop_name: "您的店铺名称"
      status: "active"

# 钉钉通知（可选）
reports:
  dingtalk_webhook: "https://oapi.dingtalk.com/robot/send?access_token=XXX"
```

#### 4. 运行程序

```bash
# 执行全流程
python main.py all

# 单独执行选品
python main.py select

# 发布商品到拼多多
python main.py publish

# 查看帮助
python main.py --help
```

---

## 📖 使用指南

### 命令说明

| 命令 | 说明 | 示例 |
|------|------|------|
| `select` | 执行 1688 选品 | `python main.py select -k 居家日用 收纳` |
| `publish` | 发布商品到拼多多 | `python main.py publish -s shop_001` |
| `orders` | 处理订单 | `python main.py orders --auto-purchase` |
| `sync` | 同步库存 | `python main.py sync` |
| `report` | 生成报表 | `python main.py report -t weekly` |
| `compliance` | 合规检测 | `python main.py compliance` |
| `all` | 执行全流程 | `python main.py all` |

### 常用参数

```bash
# 指定配置文件
python main.py select --config my_config.yaml

# 自定义选品关键词
python main.py select --keywords 数码配件 手机壳 数据线

# 指定店铺发布
python main.py publish --shop shop_002

# 设置日志级别
python main.py all --log-level DEBUG
```

### 定时任务配置

在 `config.yaml` 中配置定时任务：

```yaml
scheduler:
  enabled: true
  tasks:
    - name: "1688 选品采集"
      cron: "0 9 * * *"  # 每天 9:00
      enabled: true
    
    - name: "拼多多订单处理"
      interval: 300  # 每 5 分钟
      enabled: true
    
    - name: "生成日报"
      cron: "0 23 * * *"  # 每天 23:00
      enabled: true
```

---

## 📁 目录结构

```
ecommerce_skill/
├── main.py                 # 主程序入口
├── config.yaml             # 配置文件
├── requirements.txt        # Python 依赖
├── README.md              # 使用说明
├── modules/               # 核心模块
│   ├── selector_1688.py   # 1688 选品
│   ├── publisher_pdd.py   # 拼多多上架
│   ├── order_processor.py # 订单处理
│   ├── inventory_sync.py  # 库存同步
│   ├── report_generator.py# 报表生成
│   └── compliance_check.py# 合规检测
├── utils/                 # 工具类
│   ├── config_loader.py   # 配置加载
│   ├── excel_handler.py   # Excel 处理
│   ├── browser_manager.py # 浏览器管理
│   └── dingtalk_notify.py # 钉钉通知
├── data/                  # 数据目录
│   ├── products/          # 选品数据
│   ├── orders/            # 订单数据
│   └── reports/           # 报表输出
└── logs/                  # 日志目录
```

---

## 🔧 高级配置

### 多店铺管理

在配置文件中添加多个店铺：

```yaml
platform_pdd:
  shops:
    - shop_id: "shop_001"
      shop_name: "店铺 A"
      username: "账号 A"
      status: "active"
    
    - shop_id: "shop_002"
      shop_name: "店铺 B"
      username: "账号 B"
      status: "inactive"
```

切换店铺发布：

```bash
python main.py publish --shop shop_002
```

### 利润测算参数

调整利润计算参数：

```yaml
source_1688:
  selection:
    min_profit_margin: 30  # 最低毛利率 30%
    min_sales: 100         # 最低销量 100

platform_pdd:
  listing:
    fixed_markup_rate: 0.5  # 加价率 50%
```

### 风控参数

调整风控策略：

```yaml
compliance:
  action_delay: 3              # 操作间隔 3 秒
  max_daily_listings: 100      # 每日最大上架 100 个
  forbidden_words_check: true  # 启用违禁词检测
  advertising_law_check: true  # 启用广告法检测
```

---

## ❓ 常见问题

### Q1: 浏览器无法启动？

**A:** 确保已正确安装 Playwright 和浏览器：

```bash
pip install playwright
playwright install edge
```

### Q2: 登录状态无法保持？

**A:** 检查配置文件中的 `user_data_dir` 路径是否有写入权限，首次运行需要手动扫码登录。

### Q3: 选品数据采集不到？

**A:** 可能是网络问题或 1688 反爬限制，尝试：
- 增加操作延迟 (`action_delay`)
- 使用已登录的浏览器会话
- 降低采集频率

### Q4: 如何添加钉钉通知？

**A:** 
1. 在钉钉群中添加机器人
2. 获取 Webhook URL
3. 在 `config.yaml` 中配置：

```yaml
reports:
  notify_method: "dingtalk"
  dingtalk_webhook: "https://oapi.dingtalk.com/robot/send?access_token=XXX"
```

### Q5: 如何修改选品策略？

**A:** 编辑 `config.yaml` 中的 `selection` 参数：

```yaml
source_1688:
  selection:
    keywords: ["你的目标类目"]
    min_profit_margin: 40  # 提高毛利率要求
    min_sales: 200         # 提高销量要求
```

---

## 📝 更新日志

### v1.0.0 (2026-04-14)

- ✅ 初始版本发布
- ✅ 1688 选品模块
- ✅ 拼多多上架模块
- ✅ 订单处理模块
- ✅ 库存同步模块
- ✅ 报表生成模块
- ✅ 合规检测模块
- ✅ 多店铺管理
- ✅ 钉钉通知集成

---

## ⚠️ 使用须知

1. **合法合规使用**：请遵守各平台规则，不要用于违规用途
2. **封号风险**：虽然内置反检测机制，但高频操作仍有封号风险，建议控制操作频率
3. **API 权限**：部分功能需要平台 API 权限，如无权限会自动降级为浏览器模式
4. **数据备份**：定期备份 `data` 目录中的重要数据
5. **及时更新**：平台规则变化可能导致部分功能失效，请及时关注更新

---

## 🤝 技术支持

如有问题或建议，请联系：

- 📧 Email: support@example.com
- 💬 钉钉群：AI 团队技术支持
- 📚 文档：[在线文档链接]

---

## 📄 许可证

MIT License

---

**Made with ❤️ by AI 团队**
