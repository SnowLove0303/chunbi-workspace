---
name: omni-search
description: >
  全渠道统一搜索入口。多层协调：Brave+Exa+Tavily+Grok（search-layer）+
  17路搜索引擎（multi-search-engine）+ 百度 + GitHub。
  根据查询类型智能路由，并行检索，统一去重排序输出。
  用途：任何需要搜索的场景。不确定用什么时，直接用这个。
---

# Omni-Search v1.0 — 全渠道统一搜索协议

## 设计原则

1. **永远以 search-layer 为主通道**：Brave + Exa + Tavily + Grok 是核心，覆盖 95% 需求
2. **专业渠道专项专用**：GitHub → github-search，Baidu → baidu-search，避免主通道被污染
3. **并行不阻塞**：专业渠道与主通道并行，主通道失败时自动降级
4. **结果统一去重排序**：多源结果合并后按意图加权评分输出

## 渠道矩阵

| 渠道 | 用途 | 调用方式 | 优先级 |
|------|------|---------|--------|
| **search-layer** | 通用搜索（默认主通道） | `search.py` + `web_search` | P0 |
| **multi-search-engine** | 补充搜索、特定引擎 | `web_fetch` 17路引擎 | P1 |
| **baidu-search** | 中文搜索/百度专搜 | `web_fetch` 百度/搜狗/360 | P1 |
| **github-search-improved** | GitHub 代码/仓库/Issue | `gh search` / `gh api` | P1 |
| **github-explorer-improved** | GitHub 项目深度分析 | `gh api` + 内容抓取 | P2 |

## 意图路由表

| 意图 | 主通道 | 并行渠道 | 策略 |
|------|--------|---------|------|
| **通用搜索** | search-layer deep | multi-engine 双语扩展 | 全面覆盖 |
| **中文查询** | search-layer | baidu-search（百度/搜狗/360） | 中文优先 |
| **最新动态/新闻** | search-layer + freshness=pw | Baidu news + multi-engine 头条 | 新鲜度驱动 |
| **GitHub 代码** | github-search-improved | search-layer 辅助 | 代码专项 |
| **GitHub 项目调研** | github-explorer-improved | search-layer 补充 | 深度分析 |
| **对比分析** | search-layer × 多查询 | multi-engine 补充 | 三点对比 |
| **学术/论文** | search-layer | arxiv 路由（注：若无内容降级到 web） | 权威优先 |
| **资源/文档** | search-layer resource mode | multi-engine 官方站 | 官网优先 |
| **快速事实** | search-layer answer mode | — | Tavily AI answer |

## 执行流程

```
用户查询
    ↓
[路由判断] 识别意图 → 确定渠道组合
    ↓
[并行检索]
  ├─ search-layer（主通道，所有查询）
  ├─ 专项渠道（按需并行）
  └─ baidu-search（如是中文查询）
    ↓
[结果合并] URL去重 + 意图加权评分
    ↓
[知识合成] 结构化输出（先答案，后来源）
```

## 使用方式

### 通用搜索（默认）

直接描述你的需求，不需要指定渠道。例如：

- "帮我搜一下最新的 AI 编程工具进展"
- "查一下 RISC-V 生态目前怎么样了"
- "搜索 Vue3 和 React 的对比分析"

### 指定渠道

用 `#渠道` 标记明确指定：

- `#github "Rust 异步编程仓库"` → 强制走 github-search-improved
- `#baidu "量子计算最新进展"` → 强制走 baidu-search
- `#paper "transformer 架构优化"` → 学术论文方向

### 多渠道并行

用 `##` 要求多渠道同时搜索：

- "## 搜索 Deno 最新动态，顺便看看 GitHub 上相关项目"

## 快速命令

| 场景 | 执行 |
|------|------|
| 通用搜索 | `search-layer` 协议执行 |
| 中文增强 | search-layer + baidu-search 并行 |
| GitHub 代码 | github-search-improved |
| 全渠道深度 | omni-search 全渠道并行 |
| 最新新闻 | search-layer freshness=pw + baidu news |

## 各渠道执行细节

### search-layer（主通道）

```bash
# 标准深度搜索
python3 search.py --queries "子查询" --mode deep --intent <意图> --freshness pw --num 5

# 快速事实
python3 search.py --queries "查询" --mode answer --intent factual

# 资源定位
python3 search.py --queries "查询" --mode fast --intent resource
```

### multi-search-engine（17路引擎）

通过 `web_fetch` 调用，URL 模板：

```
Google:     https://www.google.com/search?q={keyword}
Google HK:  https://www.google.com.hk/search?q={keyword}
Bing INT:  https://cn.bing.com/search?q={keyword}&ensearch=1
Bing CN:   https://cn.bing.com/search?q={keyword}&ensearch=0
Baidu:     https://www.baidu.com/s?wd={keyword}
Sogou:     https://sogou.com/web?query={keyword}
360:       https://www.so.com/s?q={keyword}
DuckDuckGo: https://duckduckgo.com/html/?q={keyword}
Brave:     https://search.brave.com/search?q={keyword}
WolframAlpha: https://www.wolframalpha.com/input?i={keyword}
```

### baidu-search（中文专项）

```powershell
# 百度搜索
$url = "https://www.baidu.com/s?wd=" + [Uri]::EscapeDataString($query)
web_fetch($url)

# 搜狗微信（公众号内容）
$url = "https://wx.sogou.com/weixin?type=2&query=" + [Uri]::EscapeDataString($query)
web_fetch($url)

# 360 搜索
$url = "https://www.so.com/s?q=" + [Uri]::EscapeDataString($query)
```

### github-search-improved（GitHub 专项）

```bash
# 搜索仓库
gh search repos "$query" --limit 10 --sort stars

# 搜索代码
gh search code "$query" --limit 10

# 搜索 Issue
gh search issues "$query" --limit 10 --state open
```

## 中文查询增强策略

当中文查询命中以下场景时，**自动并行 baidu-search**：

1. 查询含中文且意图含"新闻/动态/最新"
2. 明确搜索国内平台（微博/微信/知乎/掘金）
3. 查询了国内公司/产品（阿里/腾讯/字节/百度/华为等）

扩展策略：中文查询同时生成英文变体，双语并行搜索。

## 降级规则

- search-layer 整体失败 → 仅用 `web_search`（Brave 单源）
- 某专项渠道失败 → 跳过该渠道，其他继续
- GitHub 渠道无 `gh` CLI → 降级到 search-layer 搜 GitHub
- 网络超时 → 重试1次，失败则降级

## 与 search-layer 的关系

- omni-search 是 search-layer 的**上层协调层**
- omni-search 调用 search-layer 执行主通道搜索
- 不替代 search-layer，避免循环依赖
- 所有 search-layer 的参数/协议完全透传
