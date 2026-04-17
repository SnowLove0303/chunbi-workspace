---
title: Hermes Agent 项目分析
tags:
  - AI-Agent
  - NousResearch
  - OpenSource
  - HermesAgent
  - 项目分析
created: 2026-04-14
source: https://github.com/NousResearch/hermes-agent
stars: 79441
license: MIT
language: Python
---

# Hermes Agent ☤

> **The self-improving AI agent built by [Nous Research](https://nousresearch.com).**
> 
> 官网: https://hermes-agent.nousresearch.com

---

## 项目概览

| 属性 | 值 |
|------|-----|
| **GitHub** | [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) |
| **Stars** | 79,441 ⭐ |
| **Fork** | 10,630 |
| **语言** | Python (15.5MB), TypeScript, Shell, Nix |
| **License** | MIT |
| **创建时间** | 2025-07-22 |
| **最后更新** | 2026-04-14 |
| **主要贡献者** | teknium1 (2795次提交) |

---

## 核心定位

**"The agent that grows with you"** — 内置学习循环的自我改进AI Agent。

Hermes Agent 是唯一一个内置**学习循环**的AI Agent：
- 从经验中创建 Skills
- 在使用中自我改进
- 自动保存知识
- 搜索历史对话
- 跨会话建立用户画像

---

## 核心特性

### 1. 多模型支持
使用任意你想要的模型：
- Nous Portal
- OpenRouter (200+ 模型)
- Xiaomi MiMo
- z.ai/GLM
- Kimi/Moonshot
- MiniMax
- Hugging Face
- OpenAI
- 或你自己的端点

切换命令：`hermes model` — 无需代码修改

### 2. 全平台接入
| 平台 | 支持情况 |
|------|---------|
| CLI (终端) | ✅ 完整TUI界面 |
| Telegram | ✅ |
| Discord | ✅ |
| Slack | ✅ |
| WhatsApp | ✅ |
| Signal | ✅ |
| Email | ✅ |

### 3. 内置学习闭环
- **Agent管理的记忆**：定期自动保存
- **自主Skill创建**：复杂任务后自动生成
- **使用中自我改进**：Skills在使用中不断优化
- **FTS5会话搜索**：LLM摘要 + 跨会话检索
- **用户建模**：基于 Honcho 的用户画像

### 4. 调度自动化
内置Cron调度器，支持自然语言配置：
- 每日报告
- 夜间备份
- 每周审计
- 完全无人值守运行

### 5. 多端部署
支持6种终端后端：
- 本地
- Docker
- SSH
- Daytona
- Singularity
- Modal

Daytone和Modal支持**无服务器持久化** — 空闲时休眠，按需唤醒，几乎零成本。

### 6. 研究支持
- 批量轨迹生成
- Atropos RL环境
- 轨迹压缩（用于训练下一代工具调用模型）

---

## 与OpenClaw的关系

- Hermes Agent 被定位为 **"超越OpenClaw的龙虾引擎"**
- 支持从 OpenClaw 平滑迁移：`hermes claw migrate`
- 使用类似的 Skills 系统（兼容 agentskills.io 开放标准）
- 在 OpenClaw 基础上增加了更多自我改进能力

---

## 安装方式

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

支持：
- Linux
- macOS
- WSL2
- Android (Termux)

> Windows不支持原生运行，需安装 WSL2

---

## 常用命令

```bash
hermes              # 交互式CLI
hermes model        # 选择模型
hermes tools        # 配置工具
hermes config set   # 设置配置
hermes gateway      # 启动消息网关
hermes setup        # 完整设置向导
hermes claw migrate # 从OpenClaw迁移
hermes update       # 更新版本
hermes doctor       # 诊断问题
```

---

## 相关项目

| 项目 | 说明 |
|------|------|
| [hermes-agent](https://github.com/NousResearch/hermes-agent) | 主项目 |
| [hermes-agent-self-evolution](https://github.com/NousResearch/hermes-agent-self-evolution) | 自我进化能力 |
| [hermes-webui](https://github.com/nesquena/hermes-webui) | Web UI界面 |
| [hermes-workspace](https://github.com/outsourc-e/hermes-workspace) | 原生Web工作区 |
| [awesome-hermes-agent](https://github.com/0xNyk/awesome-hermes-agent) | 精选资源列表 |
| [clawpanel](https://github.com/qingchencloud/clawpanel) | OpenClaw & Hermes管理面板 |
| [agency-agents-zh](https://github.com/jnMetaCode/agency-agents-zh) | 中文AI专家角色集合 |

---

## 视频来源

本笔记由B站视频《GitHub 斩获 4万星 Hermes Agent：新一代"超越OpenClaw 龙虾引擎"！》整理
- UP主: 程序员晓刘
- BV号: BV1PwDyBtEpN
- 播放: 5,385

---

*最后更新: 2026-04-14*
