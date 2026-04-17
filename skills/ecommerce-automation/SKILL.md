# 1688 选品 + 拼多多运营自动化技能

## 技能概述

**技能名称**: 1688 选品 + 拼多多运营自动化  
**版本**: 1.0.0  
**适用场景**: 无货源电商店群运营、1688 货源选品、拼多多多店铺管理  
**技术模式**: 混合模式（API + 浏览器自动化）

---

## 核心能力

### 1. 1688 智能选品
- 自动采集热销榜、新品榜商品数据
- 利润测算（考虑运费、平台扣点、快递成本）
- 供应商资质评估（诚信通年限、回头率）
- 侵权风险检测（品牌词、专利产品）
- 输出达标商品列表和采购建议

### 2. 拼多多商品上架
- 标题 SEO 优化（适配拼多多搜索规则）
- 一键发布到拼多多商家后台
- SKU 多规格定价和库存设置
- 多店铺批量上架支持
- 人工确认环节（规避行为风控）

### 3. 订单自动处理
- 实时监控拼多多新订单（每 5 分钟）
- 订单数据自动导出和归档
- 自动生成 1688 采购单
- 异常订单检测和预警
- 支持自动跳转到采购页面

### 4. 库存同步管理
- 监控 1688 供应商库存变化
- 自动调整拼多多店铺库存
- 低库存预警通知（钉钉/微信）
- 安全库存策略配置
- 滞销商品检测

### 5. 数据报表生成
- 销售日报/周报/月报自动生成
- 商品销量排行分析
- 利润统计和 ROI 计算
- 竞品价格监控
- Excel 报表推送至钉钉

### 6. 合规检测
- 违禁词自动检测
- 广告法合规检查
- 品牌侵权风险评估
- 操作频率控制（防封号）
- 单日最大上架数量限制

---

## 使用方式

### 命令行交互

```bash
# 执行全流程
python main.py all

# 单独执行选品
python main.py select --keywords 居家日用 收纳整理

# 发布商品到指定店铺
python main.py publish --shop shop_001

# 处理订单并自动采购
python main.py orders --auto-purchase

# 生成周报
python main.py report --type weekly

# 查看帮助
python main.py --help
```

### 图形化启动（Windows）

双击运行 `run.bat`，选择要执行的操作。

### 定时任务

在 `config.yaml` 中配置 Cron 表达式：

```yaml
scheduler:
  enabled: true
  tasks:
    - name: "1688 选品采集"
      cron: "0 9 * * *"  # 每天 9:00
    
    - name: "订单处理"
      interval: 300  # 每 5 分钟
    
    - name: "生成日报"
      cron: "0 23 * * *"  # 每天 23:00
```

---

## 配置说明

### 基础配置

```yaml
basic:
  name: "1688 选品 + 拼多多运营自动化"
  data_dir: "./data"
  logs_dir: "./logs"
  log_level: "INFO"
```

### 1688 选品配置

```yaml
source_1688:
  mode: "hybrid"  # api / browser / hybrid
  browser:
    type: "edge"
    headless: false  # 建议设为 false，便于扫码登录
    port: 9222
    user_data_dir: "./browser_data/1688"
  selection:
    min_profit_margin: 30  # 最低毛利率 30%
    min_sales: 100         # 最低销量 100
    keywords:
      - "居家日用"
      - "收纳整理"
```

### 拼多多店铺配置

```yaml
platform_pdd:
  mode: "hybrid"
  browser:
    type: "edge"
    port: 9223
    user_data_dir: "./browser_data/pdd"
  shops:
    - shop_id: "shop_001"
      shop_name: "店铺 A"
      status: "active"
    - shop_id: "shop_002"
      shop_name: "店铺 B"
      status: "inactive"
  listing:
    fixed_markup_rate: 0.5  # 加价率 50%
    title_suffix: "包邮 正品 热销"
```

### 钉钉通知配置

```yaml
reports:
  notify_method: "dingtalk"
  dingtalk_webhook: "https://oapi.dingtalk.com/robot/send?access_token=XXX"
```

---

## 文件结构

```
ecommerce_skill/
├── SKILL.md              # 技能说明（本文件）
├── README.md             # 详细使用文档
├── config.yaml           # 配置文件
├── requirements.txt      # Python 依赖
├── install.bat           # 安装脚本（Windows）
├── run.bat               # 快速启动脚本（Windows）
├── main.py               # 主程序入口
├── modules/              # 核心模块
│   ├── selector_1688.py    # 1688 选品
│   ├── publisher_pdd.py    # 拼多多上架
│   ├── order_processor.py  # 订单处理
│   ├── inventory_sync.py   # 库存同步
│   ├── report_generator.py # 报表生成
│   └── compliance_check.py # 合规检测
├── utils/              # 工具类
│   ├── config_loader.py    # 配置加载
│   ├── excel_handler.py    # Excel 处理
│   ├── browser_manager.py  # 浏览器管理
│   └── dingtalk_notify.py  # 钉钉通知
├── data/               # 数据目录（运行时生成）
│   ├── products/         # 选品数据
│   ├── orders/           # 订单数据
│   └── reports/          # 报表输出
└── logs/               # 日志目录（运行时生成）
```

---

## 部署步骤

### 1. 环境准备

- Windows 10/11 操作系统
- Python 3.10+（已安装 pip）
- Microsoft Edge 或 Google Chrome 浏览器

### 2. 安装依赖

**方式一：使用安装脚本（推荐）**

```bash
install.bat
```

**方式二：手动安装**

```bash
pip install -r requirements.txt
playwright install edge
```

### 3. 配置参数

编辑 `config.yaml` 文件：
- 修改选品关键词
- 配置店铺信息
- 设置钉钉 Webhook（可选）

### 4. 首次运行

```bash
# 测试选品功能
python main.py select

# 测试成功后，执行全流程
python main.py all
```

### 5. 移动到目标路径

将整个 `ecommerce_skill` 文件夹复制到：

```
F:\skill\电商运营\
```

---

## 使用说明

### 首次使用流程

1. **安装完成后**，先运行一次选品测试：
   ```bash
   python main.py select
   ```

2. **检查选品结果**：
   - 查看 `data/products/` 目录下的 Excel 文件
   - 确认利润测算是否准确
   - 调整选品参数（如需要）

3. **登录拼多多商家后台**：
   - 运行 `python main.py publish`
   - 手动扫码登录
   - 浏览器会保存登录状态

4. **小批量测试上架**：
   - 修改配置 `batch_size: 5`（先测试 5 个商品）
   - 运行 `python main.py publish`
   - 检查上架结果

5. **正式运行**：
   - 恢复正常的 batch_size（50-100）
   - 运行 `python main.py all`
   - 定期查看日志和报表

### 日常运维

**每日例行**：
- 查看日报（自动生成，推送到钉钉）
- 检查低库存预警
- 处理异常订单

**每周例行**：
- 查看周报，分析销售趋势
- 调整选品策略
- 优化定价参数

**每月例行**：
- 查看月报，核算利润
- 清理滞销商品
- 更新违禁词库

---

## 风控策略

### 行为风控规避

1. **操作间隔控制**：
   ```yaml
   compliance:
     action_delay: 3  # 每次操作间隔 3 秒
   ```

2. **单日数量限制**：
   ```yaml
   compliance:
     max_daily_listings: 100  # 每日最多上架 100 个
   ```

3. **浏览器复用**：
   - 使用 `user_data_dir` 保存登录状态
   - 避免频繁扫码触发风控

4. **人工确认环节**：
   - 上架提交前暂停，由人工确认
   - 订单采购跳转手动完成

### 内容风控规避

1. **违禁词检测**：
   - 自动检测标题和详情页
   - 内置广告法敏感词库

2. **品牌侵权检测**：
   - 识别知名品牌词
   - 标记高风险商品

3. **图片版权**：
   - 建议使用供应商授权图片
   - 或使用 AI 生成主图

---

## 常见问题

### Q1: 浏览器无法启动？
确保已安装 Playwright 和对应浏览器：
```bash
playwright install edge
```

### Q2: 登录状态无法保持？
检查 `user_data_dir` 路径是否有写入权限，首次登录后不要删除该目录。

### Q3: 选品数据采集失败？
- 检查网络连接
- 增加操作延迟参数
- 尝试降低采集频率

### Q4: 钉钉消息不推送？
- 检查 Webhook URL 是否正确
- 确认钉钉机器人已启用
- 查看防火墙设置

### Q5: 如何添加更多店铺？
在 `config.yaml` 的 `platform_pdd.shops` 数组中添加新店铺配置。

---

## 升级计划

### v1.1.0 (规划中)
- [ ] API 对接模式完善（拼多多开放平台）
- [ ] 1688 以图搜图功能
- [ ] 自动广告投放优化
- [ ] 客服自动回复集成

### v1.2.0 (规划中)
- [ ] 拓展抖音小店支持
- [ ] 拓展淘宝/天猫支持
- [ ] 机器学习选品模型
- [ ] 预测性库存管理

---

## 技术支持

- 📧 Email: support@example.com
- 💬 钉钉群：AI 团队技术支持
- 📚 在线文档：[待补充]

---

## 许可证

MIT License

**最后更新**: 2026-04-14
