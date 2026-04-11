#!/usr/bin/env python3
"""
Bilibili 视频下载示例
全链路：下载 → 合并 → 完成
"""

import sys
sys.path.insert(0, r'F:\openclaw1\.openclaw\workspace\skills\video-workflow')

from video_workflow import process_bilibili_video

# Bilibili 视频 URL
url = "https://www.bilibili.com/video/BV1oY9NBCEjR/"

# 处理视频（自动下载并合并）
output = process_bilibili_video(url, output_dir="F:/工作区间")

if output:
    print(f"\n🎉 视频已保存: {output}")
else:
    print("\n❌ 处理失败")
