---
name: unified-search
description: >
  搜索技能统一入口。根据需求自动或手动路由到最合适的搜索工具。
  整合：search-layer（默认主通道）、omni-search（全渠道）、multi-search（17路引擎）、
  github-search/explorer（GitHub）、agnxi（AI工具目录）、bailian（百炼）、browser（浏览器）。
  不确定用什么时，直接用这个。
---

# Unified Search v1.0 — 全搜索技能统一入口

## 快速选择（按需求）

| 需求 | 推荐工具 | 命令/方式 |
|------|---------|-----------|
| **通用搜索（不确定用什么）** | search-layer | `python search.py <query>` |
| **中文内容/国内网站** | omni-search | `python omni_search.py <query>` |
| **GitHub 仓库/代码搜索** | github-search | `gh search repo/code/issues <query>` |
| **GitHub 项目深度分析** | github-explorer | `python explorer.py <owner/repo>` |
| **AI工具/MCP Server目录** | agnxi-search | `python agnxi_search.py <query>` |
| **17路引擎轰炸搜索** | multi-search-engine | `python multi_search.py <query>` |
| **百度系搜索** | multi-search-engine-simple | `python simple_search.py <query>` |
| **阿里百炼搜索** | bailian-web-search | `python bailian_search.py <query>` |
| **需要打开浏览器演示** | browser-control | 浏览器自动化 |
| **综合以上全开** | omni-search deep | `python omni_search.py --depth deep <query>` |

---

## 工具矩阵

| 工具 | 核心定位 | 典型场景 |
|------|---------|---------|
| **search-layer** | 默认主通道，意图感知多源协调 | 90% 的通用搜索需求 |
| **omni-search** | 全渠道并行，按语言/类型路由 | 中文搜索、跨语言、复杂需求 |
| **multi-search-engine** | 17路引擎并行搜索 | 需要最大覆盖、结果对比 |
| **multi-search-engine-simple** | 国内10路精简引擎 | 百度/搜狗/360/神马/必应等 |
| **bailian-web-search** | 阿里百炼 API | 国内合规环境 |
| **github-search** | `gh search` CLI | 找仓库、代码片段、Issue |
| **github-explorer** | `gh api` + 内容抓取 | 项目调研、README分析、趋势 |
| **agnxi-search-skill** | Agnxi AI工具目录 | 找 AI Agent / MCP Server / Skills |
| **browser-control** | 浏览器自动化 | 需登录/需JS渲染的搜索 |
| **search-bot** | Brave实时搜索 | 快速实时新闻/热点 |

---

## 执行流程

```
用户需求
    ↓
Step 1: 判断需求类型（见 decision-tree.md）
    ↓
Step 2: 选择最优工具/工具组合
    ↓
Step 3: 执行搜索
    ↓
Step 4: 结果返回/合成
```

---

## 快速参考

```bash
# 通用搜索（推荐默认）
python skills/unified-search/scripts/search.py "人工智能最新进展"

# 全渠道深度搜索
python skills/unified-search/scripts/search.py --mode deep "量子计算"

# GitHub 代码搜索
gh search code "transformer attention" --limit 10

# GitHub 项目分析
python skills/unified-search/scripts/github_explorer.py "openai/gpt-4"

# AI 工具目录搜索
python skills/unified-search/scripts/agnxi_search.py "浏览器自动化"

# 17路引擎搜索
python skills/unified-search/scripts/multi_search.py "最新AI模型发布"

# 中文/国内内容
python skills/unified-search/scripts/search.py --lang zh "国产大模型"
```

---

## 决策树（详细）

→ 见 `references/decision-tree.md`

## 能力详情

→ 见 `references/capabilities.md`

## 快捷命令

| 命令 | 说明 |
|------|------|
| `python search.py <query>` | 通用搜索（search-layer 驱动）|
| `python search.py --mode deep <query>` | 深度搜索（全渠道并行）|
| `python search.py --mode answer <query>` | 快速事实（Tavily AI Answer）|
| `python search.py --lang zh <query>` | 中文搜索（优先国内引擎）|
