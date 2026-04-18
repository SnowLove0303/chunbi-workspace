# 搜索决策树 — 按需求选工具

## 🔍 开始

**你的搜索需求属于哪一类？**

---

## 1️⃣ 通用搜索（最常见）

> 不确定用什么、搜索目标不明确、混合类型需求

```
通用搜索
    ↓
推荐: search-layer（默认）
命令: python search.py "你的问题"
备选: omni-search --mode deep
```

✅ **选 search-layer 当：**
- 不知道用什么工具时（永远正确）
- 需要多源结果交叉验证
- 事实查询、研究、对比、分析

---

## 2️⃣ 中文内容 / 国内网站

> 搜索中文资料、国内网站、百度系内容

```
中文搜索
    ↓
推荐: omni-search（自动路由）
命令: python search.py --lang zh "中文关键词"
备选: multi-search-engine-simple（百度/搜狗/360/神马/必应）
备选: bailian-web-search（阿里百炼，合规环境）
```

✅ **选 omni-search 当：**
- 中文为主 + 需要英文结果作补充
- 不确定中文资料是否充足

✅ **选 multi-search-engine-simple 当：**
- 只需国内引擎结果
- 需要百度/搜狗/360/神马多路并行

✅ **选 bailian-web-search 当：**
- 在阿里云/国内合规环境
- 需要稳定的国内搜索结果

---

## 3️⃣ GitHub 专项

### 3A. 找仓库 / 代码片段 / Issue

```
GitHub 代码搜索
    ↓
推荐: github-search
命令: gh search code "keyword" --limit 10
备选: gh search repos "keyword" --limit 10
备选: gh search issues "keyword" --limit 10
```

### 3B. 项目深度调研

```
GitHub 项目分析
    ↓
推荐: github-explorer
命令: python github_explorer.py owner/repo
输出: README + Stars + Issues + Commits + 概述
备选: 手动 gh api + 内容抓取
```

✅ **选 github-search 当：**
- 已知关键词，找仓库/代码/Issue
- 需要快速列表式结果

✅ **选 github-explorer 当：**
- 调研某个项目的完整情况
- 需要 README 内容分析
- 看项目趋势、健康度、贡献者

---

## 4️⃣ AI 工具 / Agent / MCP Server

```
AI 工具搜索
    ↓
推荐: agnxi-search-skill
命令: python agnxi_search.py "关键词"
备选: browser-control + 访问 agnxi.com
备选: search-layer 搜索 "best AI agent for X"
```

✅ **选 agnxi-search 当：**
- 找 AI Agent 工具
- 找 MCP Server
- 找现成的 Skill/工作流

---

## 5️⃣ 最大覆盖搜索

> 需要最全面结果，不接受遗漏

```
最大覆盖搜索
    ↓
推荐: omni-search --mode deep（全渠道并行）
命令: python omni_search.py --depth deep "你的问题"
原理: search-layer + 17路引擎 + 百度 + GitHub 同时跑
```

✅ **选 deep 模式当：**
- 重要决策需要多方验证
- 研究类需求不接受遗漏
- 搜索结果可能因语言/平台分散

---

## 6️⃣ 快速事实 / 即时新闻

```
快速事实查询
    ↓
推荐: search-layer --mode answer
命令: python search.py --mode answer "今天是几号"
备选: search-bot（Brave 实时搜索）
备选: Tavily AI Answer（精确 + 引用）
```

✅ **选 answer 模式当：**
- 需要带引用来源的准确答案
- 事实性问题（日期/人物/事件）

---

## 7️⃣ 需登录 / 需 JS 渲染

```
需要登录态 / JS 渲染
    ↓
推荐: browser-control
备选: opencli（Chrome 接管模式）
```

✅ **选 browser-control 当：**
- 搜索结果需要登录才能看
- 目标网站有反爬
- 需要截图/交互的搜索任务

---

## 8️⃣ 国内合规 / 企业环境

```
国内企业环境
    ↓
推荐: bailian-web-search（阿里百炼）
备选: multi-search-engine-simple（国内引擎）
备选: omni-search（国内渠道优先）
```

---

## 决策速查表

| 需求 | 第一选择 | 第二选择 | 命令 |
|------|---------|---------|------|
| 通用搜索 | ✅ search-layer | omni-search | `python search.py "query"` |
| 中文搜索 | ✅ omni-search | multi-simple | `python search.py --lang zh "query"` |
| GitHub找仓库 | ✅ github-search | search-layer | `gh search repos "query"` |
| GitHub代码 | ✅ github-search | search-layer | `gh search code "query"` |
| 项目深度分析 | ✅ github-explorer | 手动gh api | `python explorer.py owner/repo` |
| AI工具/MCP | ✅ agnxi-search | browser+agnxi.com | `python agnxi_search.py "query"` |
| 最大覆盖 | ✅ omni-search deep | 17路引擎 | `python omni_search.py --depth deep` |
| 快速事实 | ✅ Tavily answer | search-layer | `python search.py --mode answer` |
| 登录态搜索 | ✅ browser-control | opencli | `opencli operate open <url>` |
| 国内合规 | ✅ bailian | multi-simple | `python bailian_search.py "query"` |
| 实时新闻 | ✅ search-bot | search-layer | `python search.py --mode news` |

---

## 高级技巧

### 组合搜索
```bash
# search-layer + GitHub 并行
python search.py "transformer attention" & gh search code "transformer attention" --limit 5 &
```

### 降级策略
```
search-layer 失败 → omni-search deep → multi-search-engine → 手动搜索
```

### 语言过滤
```bash
# 只看英文结果
python search.py --lang en "AI model"

# 只看中文结果
python search.py --lang zh "AI模型"
```
