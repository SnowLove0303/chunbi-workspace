# 通用浏览器开发配置 - 完整参考文档

## 第一节 执行前端口检测

Chrome CDP 9222 → 有则复用（保留登录态）/ 无则启动新浏览器
OpenClaw Gateway 18789 → 确认本地服务在线

## 第二节 脚本存放规范

1. 优先在 `F:\skill\通用浏览器控制\` 子目录下创建/修改脚本
2. 每次新建前，先扫描目标目录检查是否已有可用程序
3. 修改而非新建，避免重复脚本散落

## 第三节 工作流设计原则

- **简短**：每个步骤可独立验证，逐步通过
- **无冗余**：剔除错误步骤和无效验证
- **可恢复**：关键节点 checkpoint，失败后可从断点继续

## 第四节 工具选型

| 工具 | 场景 | Token 效率 |
|------|------|-----------|
| Playwright CLI | 高频编码 Agent | ⭐⭐⭐⭐⭐ |
| fast-playwright-mcp | 中频 AI 交互 | ⭐⭐⭐⭐ |
| playwright-mcp | 探索式自动化 | ⭐⭐⭐ |
| browser-use | 复杂 AI 任务 | ⭐⭐ |
| stagehand | 自然语言驱动 | ⭐⭐ |

## 第五节 lobster Workflow 规范

标准结构：name / settings / variables / steps（含 verify / checkpoint / on_error / always_run / approval）

## 第六节 组合模式

- 高频开发 → Playwright CLI + 脚本 + 逐步验证
- 研究型多步 → lobster + fast-playwright-mcp + diff + checkpoint
- 复杂登录态 → Browser Use Cloud
- 探索性模糊目标 → stagehand → lobster 接手

## 第七节 工具链索引

- fast-playwright-mcp: `npx @tontoko/fast-playwright-mcp@latest`
- lobster: `npm i -g @openclaw/lobster`
- browser-use: `uv add browser-use`
- stagehand: `npx create-browser-app`

## 第八节 验证层（三维验收）

三维：功能精准度 × 效率得分 × 成果达标率

| 维度 | 及格线 | 处理 |
|------|--------|------|
| 三维均 ≥ 60 | PASS | 继续 |
| 任一 40-59 | RETRY | 最多2次 |
| 任一 < 40 | ABORT | 终止 |

## 第九节 代码审核

审核脚本：`scripts/check_code.py`

检查项：语法 / 硬编码凭证 / 危险命令 / 路径规范 / timeout / 异常处理 / 依赖记录

## 第十节 重复度审查

审查脚本：`scripts/scan_duplicates.py`

阈值：≥80% 强制复用 / 60-79% 审查合并 / <40% 通过新建
