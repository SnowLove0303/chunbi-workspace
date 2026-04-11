# Bilibili AI早报自动生成器

## 功能

自动化获取指定 UP 主的最新视频，转录内容并生成结构化的 Obsidian 笔记。

## 工作流程

```
1. 获取 UP 主最新视频 → 2. 下载音频 → 3. Whisper 转录 → 4. 生成 Obsidian 笔记
```

## 使用方法

### 基本用法

```python
from bilibili_news import BilibiliNewsGenerator

# 初始化
generator = BilibiliNewsGenerator()

# 生成指定 UP 主的最新视频笔记
result = generator.generate_note(
    up_uid="285286947",      # UP 主 UID
    up_name="橘郡Juya",       # UP 主名称
    vault_path="C:/Users/chenz/Documents/Obsidian Vault"  # Obsidian 路径
)
```

### 命令行用法

```bash
# 生成笔记
python -m bilibili_news "285286947" "橘郡Juya"

# 指定输出路径
python -m bilibili_news "285286947" "橘郡Juya" --vault "D:/Obsidian/Vault"
```

## 配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `BILIbilI_VAULT_PATH` | Obsidian 笔记路径 | `C:/Users/chenz/Documents/Obsidian Vault` |
| `BILIBILI_TEMP_DIR` | 临时文件目录 | `F:/工作区间/ai_news_temp` |
| `FFMPEG_PATH` | ffmpeg 路径 | `F:/依赖/ffmpeg/ffmpeg-8.1-essentials_build/bin` |
| `WHISPER_VENV` | faster-whisper 虚拟环境 | `F:/skill/faster-whisper-skill/.venv` |
| `HF_ENDPOINT` | HuggingFace 镜像 | `https://hf-mirror.com` |

### 依赖项

- Python 3.10+
- yt-dlp
- faster-whisper
- ffmpeg
- Obsidian Vault

## 笔记输出格式

```markdown
---
date: 2026-04-03
source: Bilibili
up: UP主名称
video: 视频标题
url: https://www.bilibili.com/video/BVxxx
tags:
  - AI早报
  - 实时快报
---

# 视频标题

## 视频信息
- 时长
- BV ID
- UP主
- 标签

## 今日要点
- 1. 要点1
- 2. 要点2

## 详细内容
### 1. 主题1
- 详细描述...

### 2. 主题2
- 详细描述...
```

## 特性

- ✅ 自动获取最新视频
- ✅ 支持指定 UP 主
- ✅ 自动转录音频
- ✅ 生成结构化笔记
- ✅ 跳过已处理视频
- ✅ 支持批量处理

## 安装

```bash
# 安装依赖
pip install yt-dlp faster-whisper

# 配置环境变量（可选）
export BILIBILI_VAULT_PATH="你的Obsidian路径"
```

## 注意事项

1. 首次运行需要下载 Whisper 模型（约 39MB）
2. 确保 ffmpeg 已安装并配置到 PATH
3. 网络不稳定时可以设置重试次数
