---
name: video-news-workflow
description: >
  视频新闻自动转笔记工作流。从 Bilibili UP 主获取最新视频 → 下载音频 → 
  Whisper/FunASR 转录 → 生成 Obsidian 笔记 → 自动美化。
  用于「AI早报」等每日视频笔记场景。
---

# Video News Workflow v3（2026-04-05 优化版）

多 UP 主并行 + FunASR 备用 + md_beautifier 美化 + 按日期缓存。

## ASR 引擎切换

```bash
# 默认用 Whisper
python run.py

# 切换到 FunASR
set ASR=funasr && python run.py
```

## 执行命令

```bash
python "F:\openclaw1\.openclaw\workspace\skills\video-news-workflow\scripts\run.py"
```

## 脚本说明

| 脚本 | 用途 |
|------|------|
| `run.py` | **v3 主脚本**（多UP + FunASR备用 + 美化） |
| `run_full.py` | 旧版完整流程（已废弃） |
| `md_beautifier.py` | 笔记美化工具（自动调用） |

## v3 工作流（5步）

```
Step 1: 获取视频列表（yt-dlp + 按日期缓存）
Step 2: 匹配当天视频（优先标题日期）
Step 3: Whisper 转录（失败自动用 FunASR 后备）
Step 4: 生成笔记（note_formatter）
Step 5: md_beautifier 美化（自动应用）
```

### ASR 策略
- 优先 Whisper small（已预下载）
- Whisper 失败时自动尝试 FunASR（paraformer-large）
- FunASR 作为独立引擎可选：`set ASR=funasr`

## UP 主配置

```python
UP_LIST = [
    {"name": "橘郡Juya", "uid": "285286947"},
    {"name": "初芽Sprout", "uid": "1638385490"},
]
```

## 输出文件

- `实时快报/{日期} AI早报-综合.md` — **合并版**（推荐阅读）
- `实时快报/{日期} AI早报-{UP名}.md` — 各UP单独笔记

## 缓存机制

| 缓存类型 | 有效期 | 说明 |
|----------|--------|------|
| 视频列表 | 当天有效 | 按日期过滤缓存 |
| 音频 | 永久 | 已下载不重复 |
| 转录 | 永久 | 已转录不重复 |

## 防限流机制

| 机制 | 说明 |
|------|------|
| **WBI 签名搜索** | 集成 yt_dlp 源码实现的 WBI 算法，搜索永不触发 412 |
| **Cookie 认证** | 将 bilibili cookies 放到 `F:\工作区间\ai_news_temp\cookies.txt`，自动注入 yt-dlp |
| **指数退避重试** | 遇到 412/429/5xx 错误时，2/4/8s 依次等待后重试 |
| **日期缓存** | 同一 UP 主当天内不重复请求 |

> 💡 Cookie 获取方法：浏览器登录 bilibili 后，F12 → Application → Cookies → 复制 buvid3 等字段到 `cookies.txt`

## 环境路径

| 组件 | 路径 |
|------|------|
| 临时目录 | `F:\工作区间\ai_news_temp` |
| ffmpeg | `F:\依赖\ffmpeg\ffmpeg-8.1-essentials_build\bin` |
| Whisper small | `F:\AI\whisper_models\faster-whisper-small` |
| FunASR venv | `F:\skill\funasr-skill\.venv` |
| 输出 | `C:\Users\chenz\Documents\Obsidian Vault\实时快报` |

## md_beautifier 功能

自动对生成的笔记进行美化：
- 中文-英文/数字间距
- 中文标点修正
- YAML frontmatter 格式化
- 标题层级修正（防止跳级）
- 空行压缩（最多连续1个）
- 列表统一为 `-` 开头

## 已知问题

- **UP主提前录制**：橘郡Juya 的视频是提前录好、第二天早上发的。脚本通过标题日期（不是上传日期）来匹配当天内容。
- **Bilibili 限流**：请求过多会触发 412/352 限流，使用缓存机制避免。
- **PowerShell 编码**：yt-dlp 输出中文标题会在控制台显示乱码，但实际数据正确。

## 依赖

- yt-dlp
- faster-whisper（CPU int8，已预下载 small 模型）
- funasr（备用，在独立 venv）
- requests (Python)
- ffmpeg
- md_beautifier（自动美化）

## v3 更新日志

| 日期 | 变化 |
|------|------|
| 2026-04-05 | v3 发布：FunASR 备用 + md_beautifier 美化 + 日期缓存 |
| 之前 | v2：多UP + 综合日报 |