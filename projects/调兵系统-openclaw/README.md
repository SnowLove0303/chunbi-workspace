# 调兵系统（OpenClaw-Commander）

## 是什么

以 `Codex` 为总司令，通过 `assistant-hub.ps1` 统一调度 `CoPaw` / `OpenClaw` / `OpenCode` 三个兵团的自动化多 Agent 协作系统。

## 测试时间

2026-04-12

## 测试结果

### ✅ 可用命令

| 命令 | 功能 |
|------|------|
| `status` | 三兵总体状态 |
| `scenario check` | 快速体检 |
| `list-openclaw-agents` | OpenClaw roster（4个agent） |
| `list-copaw-agents` | CoPaw roster（8个agent） |
| `openclaw / copaw / opencode [args]` | 透传原命 |
| `recommend` | 自动判断编队（⚠️ 偶发SIGKILL） |

### ⚠️ 已知问题

1. **SIGKILL**：`recommend` 偶发 SIGKILL（CLI WS Bug #47133），建议优先用 `auto` 代替
2. **CoPaw 中文乱码**：PowerShell 默认 GBK 编码导致 workspace 路径乱码，加 `chcp 65001` 可解

## OpenClaw Agent Roster（实测）

```
main           F:\openclaw1\.openclaw\workspace
codex-commander  F:\openclaw\workspaces\codex-commander
codex-reviewer  F:\openclaw\workspaces\codex-reviewer
codex-writer    F:\openclaw\workspaces\codex-writer
```

## 快速选型

```
小任务 → auto
对比   → swarm
稳定交付 → commander codex
重型   → formation openclaw-heavy / clawteam-*
```

## 文档

- [调兵系统使用说明-2026-04-10.md](调兵系统使用说明-2026-04-10.md) — 详细命令手册
- [调兵系统说明-2026-04-09.md](调兵系统说明-2026-04-09.md) — 架构概述
