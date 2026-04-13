# 四工具详解：Playwright MCP / lobster / browser-use / stagehand

> 2026-04-12 | GitHub 深度调研 | ⭐ 更新自社区最新实践

---

## 1. Playwright MCP ⭐26k+

**微软官方的 MCP 浏览器自动化服务器**

| 维度 | 详情 |
|------|------|
| **定位** | MCP 协议执行层（CDP 驱动） |
| **stars** | 26,494 |
| **技术** | TypeScript，Node.js 18+ |
| **核心差异** | 基于 accessibility tree，**无需视觉模型** |
| **工具数** | 22 个 MCP tools |
| **安装** | `npx @playwright/mcp@latest` |

**三大卖点：**
- **Fast & Lightweight**：纯结构化数据，token 消耗低
- **Deterministic**：避免截图 AI 的歧义性
- **广泛兼容**：VS Code / Cursor / Windsurf / Claude Desktop / Goose / Junie / Codex / Copilot / Gemini CLI / opencode 等 20+ IDE

**关键 CLI 参数：**
```
--browser chrome|firefox|webkit|msedge   # 浏览器引擎
--cdp-endpoint        # 连接已有浏览器
--caps vision|pdf|devtools  # 扩展能力
--allowed-hosts       # 安全边界
--codegen typescript|none  # 代码生成
```

**架构建议：**
- **CLI + SKILLs**：高频编码 Agent 推荐（token 效率高）
- **MCP**：探索式自动化、长对话、持久化状态场景

---

## 2. lobster ⭐1.1k

**OpenClaw 原生工作流引擎（TypeScript）**

| 维度 | 详情 |
|------|------|
| **定位** | OpenClaw 工作流编排层 |
| **stars** | 1,100 |
| **技术** | TypeScript，Node.js |
| **文件格式** | `.lobster`（YAML 子集） |
| **最新版本** | v2026.4.6 |

**核心命令：**
```
exec           # 执行 OS 命令
where/pick/head  # 数据整形
json/table     # 渲染输出
approve        # 审批门（TTY 或 --emit）
llm.invoke     # 调用 LLM
```

**工作流文件示例：**
```yaml
name: jacket-advice
args:
  location:
    default: Phoenix
steps:
  - id: fetch
    run: weather --json ${location}

  - id: confirm
    approval: Want jacket advice?
    stdin: $fetch.json

  - id: advice
    pipeline: llm.invoke --prompt "Should I wear a jacket?"
    stdin: $fetch.json
    when: $confirm.approved
```

**三大特性：**
- **Typed pipelines**：JSON-first，非文本管道
- **Approval gates**：人工审批点，支持身份约束
- **Visualization**：`lobster graph --format mermaid` 生成流程图

---

## 3. browser-use ⭐87.4k

**让网站能被 AI Agent 操控（Python）**

| 维度 | 详情 |
|------|------|
| **定位** | AI Agent 驱动的浏览器自动化（应用层） |
| **stars** | **87,400**（浏览器 Agent 领域第一） |
| **技术** | Python 3.11+，Playwright 驱动 |
| **最新版本** | 0.12.6（123 releases） |

**两种模式：**

| | 开源版 | 云版（Browser Use Cloud） |
|--|-------|--------------------------|
| 定位 | 自托管 Agent | 全托管 stealth browser |
| 能力 | 基础任务 | 复杂任务、proxy rotation、CAPTCHA |
| 集成 | 自建 | 1000+（Gmail/Slack/Notion 等） |
| 价格 | 免费（需自备 LLM API） | 按 token 计费 |

**快速开始：**
```bash
uv init && uv add browser-use
uvx browser-use init --template default
```

```python
from browser_use import Agent, Browser, ChatBrowserUse
import asyncio

async def main():
    agent = Agent(
        task="Find the number of stars of browser-use repo",
        llm=ChatBrowserUse(),
        browser=Browser(),
    )
    await agent.run()
```

**CLI（Browser Use CLI 2.0）：**
```bash
browser-use open https://example.com   # 导航
browser-use state                       # 查看可点击元素
browser-use click 5                    # 点击元素
browser-use type "Hello"               # 输入
browser-use screenshot page.png         # 截图
```

---

## 4. stagehand ⭐22k

**Browserbase 出品的 AI 浏览器自动化框架（TypeScript）**

| 维度 | 详情 |
|------|------|
| **定位** | AI + 代码双模式浏览器自动化 |
| **stars** | 22,000 |
| **技术** | TypeScript + CDP |
| **最新版本** | stagehand-server-v3 v3.6.3 |

**三大核心方法：**
```typescript
// 1. act() - 执行单个动作
await stageblind.act("click on the stageblind repo");

// 2. agent() - 多步骤任务
const agent = stageblind.agent();
await agent.execute("Get to the latest PR");

// 3. extract() - 结构化数据提取
const { author, title } = await stageblind.extract(
  "extract author and title of the PR",
  z.object({
    author: z.string(),
    title: z.string(),
  })
);
```

**三大差异化特性：**
1. **Code ↔ Natural Language 混合**：熟悉页面用代码，不熟悉的用自然语言
2. **Auto-caching + Self-healing**：网站变了自己修，不用重新跑 LLM
3. **Preview AI actions**：执行前先预览，确认再跑

---

## 横评对比

| 维度 | Playwright MCP | lobster | browser-use | stagehand |
|------|---------------|---------|-------------|-----------|
| **层级** | 执行层（协议） | 编排层 | 应用层（Agent） | 应用层 |
| **语言** | TypeScript | TypeScript | Python | TypeScript |
| **⭐** | 26k | 1.1k | **87k** | 22k |
| **核心机制** | CDP accessibility tree | YAML 工作流 | AI Agent 自主决策 | act/agent/extract |
| **视觉模型** | ❌ 不需要 | — | ✅ 可选 | ✅ 可选 |
| **人工审批** | ❌ | ✅ Approval gates | ❌ | ❌ |
| **云端托管** | ❌ | ❌ | ✅ Browser Use Cloud | ✅ Browserbase |
| **学习成本** | 低 | 中 | 低 | 中 |

---

## 重要新发现

### fast-playwright-mcp（⭐优化 fork）

微软官方版的性能优化分支，**推荐使用**：

| 特性 | 效果 |
|------|------|
| Batch 执行 | 一次 MCP 调用执行多个操作 |
| Diff 检测 | 仅返回页面变化，节省 70-80% token |
| 快照控制 | `includeSnapshot: false` 跳过页面快照 |
| 诊断工具 | `browser_diagnose` 页面分析 + 性能指标 |

### HyperAgent（⭐1.3k）

TypeScript，双模式（pagePerform 单步 + pageAI 多步），支持 MCP + action 缓存

### Playwright CLI

高频 Agent 推荐，比 MCP **token 效率更高**，因为：
- MCP 需要加载完整 tool schema（每次都要）
- CLI 命令即执行，无协议开销
