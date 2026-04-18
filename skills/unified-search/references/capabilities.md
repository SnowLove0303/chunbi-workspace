# 各搜索工具能力详情

---

## 1. search-layer（主通道）

**路径**: `workspace/skills/search-layer/scripts/search.py`

### 核心能力
- 四源并行：Brave Search + Exa + Tavily + Grok
- **意图感知**：自动分类查询类型，调整搜索策略和权重
- 结果去重 + 意图加权评分
- 支持多种模式：`fast` / `deep` / `answer`

### 支持的查询类型
| 类型 | 策略 | 说明 |
|------|------|------|
| 事实类 | Tavily answer | 带引用来源的精确答案 |
| 新闻类 | 时间排序 | 最新优先 |
| 研究类 | 多源综合 | 全面覆盖 |
| 代码类 | Exa code filter | GitHub/StackOverflow优先 |
| 对比类 | 多查询并行 | 三点对比格式 |
| 资源类 | 官网优先 | 官方文档/工具优先 |

### API Keys
```
TAVILY_API_KEY        # 刚更新为 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
BRAVE_API_KEY         # via web_search
EXA_API_KEY           # via environment
GROK_API_KEY          # via environment
```

### 使用示例
```bash
python skills/search-layer/scripts/search.py "最新大模型发布"          # 深度搜索
python skills/search-layer/scripts/search.py --mode answer "什么是RAG"  # 快速事实
python skills/search-layer/scripts/search.py --freshness pw "AI新闻"   # 本周新闻
```

---

## 2. omni-search（全渠道入口）

**路径**: `workspace/skills/omni-search/scripts/omni_search.py`

### 核心能力
- search-layer + 17路引擎 + 百度 + GitHub 全开并行
- 按语言自动路由（中文优先国内渠道）
- 统一去重排序
- 三层降级：主通道 → 专项 → 17路引擎

### 渠道详情
| 渠道 | 类型 | 备注 |
|------|------|------|
| search-layer | AI协调层 | 主通道 |
| 百度 | 中文搜索 | 国内 |
| 搜狗 | 中文搜索 | 国内 |
| 360 | 中文搜索 | 国内 |
| 神马 | 中文搜索 | 国内 |
| 必应 | 双语 | Microsoft |
| DuckDuckGo | 英文 | 隐私搜索 |
| Google | 英文 | 需代理 |
| GitHub | 代码/仓库 | gh CLI |
| ... | 共17路 | |

### 使用示例
```bash
python skills/omni-search/scripts/omni_search.py "国产大模型"    # 中文优先
python skills/omni-search/scripts/omni_search.py --depth deep "AI研究"  # 最大覆盖
```

---

## 3. multi-search-engine（17路引擎）

**路径**: `workspace/skills/multi-search-engine/scripts/multi_search.py`

### 核心能力
- 17个搜索引擎同时搜索
- 纯 HTTP 请求，无需认证
- 并行执行，结果按相关性排序
- 支持语言过滤

### 17路引擎列表
```
国内:   百度 / 搜狗 / 360搜索 / 神马搜索 / 必应(国内)
海外:   Google / DuckDuckGo / Yahoo / Ask / AOL
专业:   WolframAlpha / JSTOR / arXiv / Google Scholar
其他:   Ecosia(环保) / Baidu(双重) / Naver / DuckGoGo
```

### 使用示例
```bash
python skills/multi-search-engine/scripts/multi_search.py "AI模型对比"
python skills/multi-search-engine/scripts/multi_search.py --lang en "GPT-4"
```

---

## 4. multi-search-engine-simple（国内精简10路）

**路径**: `workspace/skills/multi-search-engine-simple/scripts/simple_search.py`

### 核心能力
- 10个国内主流引擎精简版
- 轻量快速
- 中文友好

### 10路引擎
```
百度 / 搜狗 / 360搜索 / 神马 / 必应(国内) /
Google(代理) / DuckDuckGo / 夸克 / 头条搜索 / 微博搜索
```

---

## 5. github-search（免API）

**路径**: `openclaw-skills/skills/github-search/`

### 核心能力
- `gh search` CLI 驱动，完全免费
- 三种搜索：repos / code / issues
- 支持过滤：语言、 stars、日期
- 无 API 配额限制

### 使用示例
```bash
gh search repos "transformer attention" --sort stars --limit 10
gh search code "def train" --lang python --limit 10
gh search issues "bug" --label bug --limit 10
```

---

## 6. github-explorer（免API）

**路径**: `openclaw-skills/skills/github-explorer/`

### 核心能力
- `gh api` 驱动，项目深度分析
- 自动抓取：README、Stars、Forks、Issues、Contributors
- 生成项目概述和健康度报告
- 无 API 配额限制（60 req/hr 匿名）

### 使用示例
```bash
python skills/github-explorer/scripts/explore.py openai/gpt-4
python skills/github-explorer/scripts/explore.py anthropic/claude-code
```

### 输出内容
- 项目基本信息（描述、语言、Stars）
- README 摘要
- 最近更新 / Releases
- Open Issues 数量
- 贡献者活跃度

---

## 7. agnxi-search（AI工具目录）

**路径**: `workspace/skills/agnxi-search-skill/`

### 核心能力
- Agnxi.com AI工具目录搜索
- 找 AI Agent / MCP Server / Skills
- 按分类筛选
- 包含工具描述和链接

### 使用示例
```bash
python skills/agnxi-search-skill/scripts/agnxi_search.py "浏览器自动化"
python skills/agnxi-search-skill/scripts/agnxi_search.py "MCP server"
```

---

## 8. bailian-web-search（百炼API）

**路径**: `workspace/skills/bailian-web-search/`

### 核心能力
- 阿里百炼 Web Search API
- 国内合规环境使用
- 需要 API Key

### 使用示例
```bash
python skills/bailian-web-search/scripts/bailian_search.py "中文搜索内容"
```

---

## 9. browser-control（浏览器自动化）

**路径**: `workspace/skills/browser-control/`

### 核心能力
- Playwright 驱动浏览器
- 支持登录态搜索
- JS 渲染页面抓取
- 截图/交互任务

### 使用场景
- 需要登录的网站搜索
- 反爬网站的搜索任务
- 需要 JS 渲染才能获取内容
- 演示/截图类搜索任务

---

## 10. search-bot（Brave实时）

**路径**: `workspace/skills/search-bot/`

### 核心能力
- Brave Search API 实时搜索
- 快速新闻/热点
- 需要 AIPROX_TOKEN

### 使用示例
```bash
python skills/search-bot/scripts/search_bot.py "实时热点"
```

---

## API Key 配置位置

| 服务 | 配置位置 | 备注 |
|------|---------|------|
| Tavily | `~/.openclaw/credentials/search.json` | ✅ 已配置 |
| Brave | 环境变量 BRAVE_API_KEY | |
| Exa | 环境变量 EXA_API_KEY | |
| Grok | 环境变量 GROK_API_KEY | |
| Bailian | `~/.openclaw/credentials/bailian.json` | |
| Agnxi | 无需Key | 目录搜索 |
| GitHub | `gh auth status` | ✅ 已认证 |
