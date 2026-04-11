---
name: video-workflow
description: >
  全链路视频处理工作流。包含：视频下载（Bilibili/YouTube等）、
  音视频合并、视频分析。自动管理 ffmpeg 安装。
---

# Video Workflow Skill

全链路视频处理解决方案。

## 功能

1. **视频下载** - 支持 Bilibili、YouTube、Twitter/X 等 1800+ 平台
2. **音视频合并** - 自动下载并使用 ffmpeg 合并
3. **视频分析** - 提取关键帧、字幕、转录

## 安装

```bash
# 首次使用时会自动下载 ffmpeg（约 80MB）
python setup.py
```

## 使用

### 下载视频
```python
from video_workflow import download_video
download_video("https://www.bilibili.com/video/BVxxxxx", output_dir="F:\\下载")
```

### 合并音视频
```python
from video_workflow import merge_video_audio
merge_video_audio("video.mp4", "audio.m4a", "output.mp4")
```

### 完整工作流
```python
from video_workflow import process_video
process_video("https://www.bilibili.com/video/BVxxxxx", "F:\\输出")
# 自动下载、合并、分析
```

## 依赖

- Python 3.8+
- yt-dlp
- ffmpeg（自动安装）

## 目录结构

```
video-workflow/
├── SKILL.md
├── setup.py              # 环境初始化
├── video_workflow/
│   ├── __init__.py
│   ├── downloader.py     # 视频下载
│   ├── merger.py         # 音视频合并
│   ├── analyzer.py       # 视频分析
│   └── ffmpeg_manager.py # ffmpeg 自动管理
└── examples/
    └── bilibili_download.py
```
