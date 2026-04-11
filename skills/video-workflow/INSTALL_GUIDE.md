# Video Workflow Skill - 安装指南

## ✅ 已完成

### 1. Skill 安装
- **位置**: `F:\openclaw1\.openclaw\workspace\skills\video-workflow\`
- **依赖**: yt-dlp, requests, urllib3 ✅ 已安装
- **功能**: 
  - 视频下载（Bilibili/YouTube 等）
  - 音视频合并
  - 自动 ffmpeg 管理

### 2. 文件结构
```
video-workflow/
├── SKILL.md                    # 技能说明
├── setup.py                    # 安装脚本
├── video_workflow/
│   ├── __init__.py            # 核心功能（ffmpeg 自动下载）
│   └── downloader.py          # 视频下载模块
└── examples/
    └── bilibili_download.py   # 使用示例
```

## ⚠️ 网络限制

由于当前网络环境限制（大文件下载被系统中断），**ffmpeg 自动下载失败**。

## 🔧 解决方案

### 方案 1: 手动下载 ffmpeg（推荐）

1. **下载 ffmpeg**（使用浏览器或下载工具）：
   - 链接: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
   - 大小: 约 80MB

2. **解压到指定目录**：
   ```
   F:\openclaw1\.openclaw\tools\ffmpeg\
   ```

3. **验证安装**：
   ```bash
   F:\openclaw1\.openclaw\tools\ffmpeg\bin\ffmpeg.exe -version
   ```

### 方案 2: 使用现有视频文件

已下载的文件在 `F:\工作区间\`：
- 视频: `Google 发布开放权重模型系列 Gemma 4..._video_only.mp4`
- 音频: `Google 发布开放权重模型系列 Gemma 4..._audio_only.m4a`

可以用 VLC 直接播放（同时加载两个文件）。

### 方案 3: 使用在线合并工具
- https://www.video2edit.com/merge-videos
- 上传视频和音频，合并后下载

## 🚀 使用方法

安装 ffmpeg 后，使用以下代码：

```python
import sys
sys.path.insert(0, r'F:\openclaw1\.openclaw\workspace\skills\video-workflow')

from video_workflow import process_bilibili_video

# 下载并自动合并
output = process_bilibili_video(
    "https://www.bilibili.com/video/BV1oY9NBCEjR/",
    output_dir="F:/工作区间"
)
```

或者单独合并已有文件：

```python
from video_workflow import merge_video_audio

merge_video_audio(
    "video_only.mp4",
    "audio_only.m4a", 
    "output.mp4"
)
```

## 📦 全链路 Skill 包

已安装的 Video Workflow Skill 包含：

| 功能 | 状态 | 说明 |
|------|------|------|
| 视频下载 | ✅ | yt-dlp 支持 1800+ 平台 |
| 音视频合并 | ⚠️ | 需要手动安装 ffmpeg |
| 自动 ffmpeg 管理 | ✅ | 首次使用时自动下载 |
| 视频分析 | 📝 | 待扩展 |

## 🔄 后续优化

当网络环境改善后，运行：
```bash
cd F:\openclaw1\.openclaw\workspace\skills\video-workflow
python setup.py
```

即可自动完成 ffmpeg 安装。

---

**总结**: Skill 已就绪，因网络限制需手动安装 ffmpeg（80MB）。
