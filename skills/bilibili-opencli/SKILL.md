# Bilibili OpenCLI Workflow Skill

**功能**：用 `opencli bilibili` 命令搜索 → 下载 → Whisper/FunASR 转录 → 生成 Obsidian 笔记  
**支持**：批量处理、多UP主、日期过滤

---

## 环境依赖

- **opencli**: `C:\Users\chenz\AppData\Roaming\npm\opencli.cmd`（已安装）
- **yt-dlp**: opencli 内置（视频下载）
- **Whisper**: `F:\AI\whisper_models\faster-whisper-small`（本地模型，优先）
- **FunASR**: `F:\skill\funasr-skill\.venv`（兜底引擎）
- **输出目录**: `F:\工作区间\ai_news_temp`
- **Obsidian**: `C:\Users\chenz\Documents\Obsidian Vault\实时快报`

---

## 命令行用法

### 搜索 + 下载 + 转录（单UP主，当日视频）

```powershell
python scripts/run.py --uid 285286947 --limit 5 --date 2026-04-09
```

### 关键词搜索（所有UP主）

```powershell
python scripts/run.py --search "AI 早报" --limit 5
```

### 只搜索，不下载/转录

```powershell
python scripts/run.py --uid 285286947 --limit 5 --date 2026-04-09 --dry-run
```

### 跳过转录（只要下载）

```powershell
python scripts/run.py --uid 285286947 --limit 3 --skip-transcribe
```

### 强制重转（覆盖已有txt）

```powershell
python scripts/run.py --uid 285286947 --limit 3 --force-transcribe
```

### 批量多UP（示例）

```powershell
python scripts/run.py --uid 285286947 --limit 3 --date 2026-04-09
python scripts/run.py --uid 1638385490 --limit 3 --date 2026-04-09
```

---

## 核心模块

### bilibili_utils.py — OpenCLI 封装

```python
from bilibili_utils import search_videos, get_user_videos

# 关键词搜索
results = search_videos('AI 大模型', limit=10)

# UP 主视频列表
videos = get_user_videos('285286947', limit=20)
```

返回字段: `bvid, title, author, score, url, plays, date, source`

### download.py — 批量下载

```python
from download import download_batch

results = download_batch(videos, output_dir, parallel=2, skip_existing=True)
# 返回: [{bvid, title, status, files: {.mp4, .m4a, .jpg}}]
```

### transcribe.py — 转录（Whisper 优先，FunASR 兜底）

```python
from transcribe import transcribe, transcribe_batch

# 单个
r = transcribe('BV11jDnBfErS', skip_existing=True)
print(r['text'], r['status'])

# 批量
results = transcribe_batch(bvid_list, parallel=2)
```

引擎策略:
1. Whisper small（本地模型 `F:\AI\whisper_models\faster-whisper-small`）
2. FunASR SenseVoice（`F:\skill\funasr-skill\.venv`，Whisper 失败时兜底）

### formatter.py — Obsidian 笔记生成

```python
from formatter import generate_daily_summary

summary = generate_daily_summary(videos, temp_dir=OUTPUT, vault_path=VAULT)
# 写入: {vault_path}/{date} AI早报-{UP名}.md
```

---

## run.py 主入口参数

| 参数 | 说明 |
|------|------|
| `--uid` | UP 主 UID |
| `--search` | 关键词搜索（与 --uid 二选一） |
| `--limit` | 获取视频数量（默认 5） |
| `--date` | 日期过滤（格式 YYYY-MM-DD） |
| `--output` | 下载目录（默认 `F:\工作区间\ai_news_temp`） |
| `--vault` | Obsidian 路径（默认 `C:\Users\chenz\Documents\Obsidian Vault\实时快报` |
| `--parallel` | 并行下载/转录数（默认 1） |
| `--dry-run` | 只打印，不下载/转录 |
| `--skip-transcribe` | 跳过转录 |
| `--skip-download` | 跳过下载 |
| `--force-transcribe` | 强制重转（覆盖已有 txt） |

---

## 已知问题

- **PowerShell 控制台编码**: 中文显示乱码是 PowerShell 问题，不影响文件写入。 Obsidian 文件正常显示。
- **Whisper 模型**: medium 模型需要网络下载，当前环境只有 small 可用。如需 medium，设置 `ASR_ENGINE=funasr` 强制使用 FunASR。
