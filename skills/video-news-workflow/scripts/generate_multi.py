#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video News Workflow - 多UP主版本
遍历多个UP主，获取当日视频 → 转录 → 生成 Obsidian 笔记
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import json
import subprocess
import requests
from datetime import datetime, date

# ======================= 配置：多个UP主 =======================
UP_LIST = [
    {"name": "橘郡Juya", "uid": "285286947"},
    {"name": "初芽Sprout", "uid": "1638385490"},
]

VAULT_PATH = r"C:\Users\chenz\Documents\Obsidian Vault"
OUTPUT_DIR = os.path.join(VAULT_PATH, "实时快报")
TEMP_DIR = r"F:\工作区间\ai_news_temp"
FFMPEG_BIN = r"F:\依赖\ffmpeg\ffmpeg-8.1-essentials_build\bin"
WHISPER_VENV = r"F:\skill\faster-whisper-skill\.venv"

# ======================= 工具函数 =======================
def run_cmd(cmd, env=None, timeout=120):
    if env is None:
        env = os.environ.copy()
    else:
        env = {**os.environ.copy(), **env}
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        env=env, encoding='utf-8', errors='replace', timeout=timeout
    )
    return result

def detect_date_from_title(title: str):
    """从标题提取日期"""
    m = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', title)
    if m:
        return m.group(1).replace('/', '-')
    return None

def get_video_info(bvid: str) -> dict:
    """获取视频详细信息（含简介）"""
    url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        data = r.json()
        if data['code'] == 0:
            d = data['data']
            owner = d.get('owner') or {}
            return {
                'title': d.get('title', ''),
                'author': owner.get('name', ''),
                'desc': d.get('desc', ''),
                'duration': d.get('duration', 0),
                'url': f"https://www.bilibili.com/video/{bvid}"
            }
    except:
        pass
    return {}

def fetch_latest_videos(uid: str, limit: int = 5):
    """获取最新视频列表"""
    api = f"https://api.bilibili.com/x/space/arc/search?mid={uid}&pn=1&ps={limit}&order=pubdate"
    try:
        r = requests.get(api, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        data = r.json()
        if data['code'] == 0:
            return data['data']['list']['vlist']
    except:
        pass
    return []

def download_audio(bvid: str, temp_dir: str) -> str:
    """下载音频"""
    out_file = os.path.join(temp_dir, f"audio_{bvid}.m4a")
    if os.path.exists(out_file):
        return out_file
    cmd = [
        'python', '-m', 'yt_dlp',
        '-f', 'bestaudio',
        '-o', out_file,
        '--no-playlist',
        f'https://www.bilibili.com/video/{bvid}'
    ]
    result = run_cmd(' '.join(cmd), timeout=120)
    return out_file if os.path.exists(out_file) else None

def transcribe_audio(audio_file: str, model_name: str = "small") -> str:
    """Whisper 转录"""
    txt_file = audio_file.replace('.m4a', '_whisper.txt')
    if os.path.exists(txt_file):
        with open(txt_file, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

    # 使用 faster-whisper
    script = r'F:\skill\faster-whisper-skill\scripts\transcribe.py'
    py_exe = os.path.join(WHISPER_VENV, 'Scripts', 'python.exe')

    cmd = f'"{py_exe}" "{script}" "{audio_file}" --model {model_name}'
    result = run_cmd(cmd, timeout=600)
    if result.returncode == 0 and os.path.exists(txt_file):
        with open(txt_file, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    return ""

def find_today_video(videos: list, target_date: str):
    """在视频列表中找当天日期的视频"""
    for v in videos:
        title_date = detect_date_from_title(v['title'])
        if title_date == target_date:
            return v
    return videos[0] if videos else None

# ======================= 主流程 =======================
def process_up(up: dict, target_date: str):
    """处理单个UP主"""
    name = up['name']
    uid = up['uid']
    print(f"\n{'='*50}")
    print(f"处理 UP: {name} (UID: {uid})")
    print(f"{'='*50}")

    videos = fetch_latest_videos(uid, limit=5)
    if not videos:
        print(f"[WARN] {name}: 未获取到视频")
        return None

    # 找当天视频
    today_video = find_today_video(videos, target_date)
    if not today_video:
        print(f"[WARN] {name}: 未找到 {target_date} 的视频，使用最新: {videos[0]['title']}")
        today_video = videos[0]

    bvid = today_video['bvid']
    title = today_video['title']

    # 优先从视频简介获取内容
    info = get_video_info(bvid)
    desc = info.get('desc', '')

    # 合并标题日期
    title_date = detect_date_from_title(title) or target_date

    print(f"[{name}] 当日视频: {title}")

    # 下载音频
    print(f"[{name}] 下载音频...")
    audio_file = download_audio(bvid, TEMP_DIR)
    if not audio_file:
        print(f"[FAIL] {name}: 音频下载失败")
        return None

    # 转录
    print(f"[{name}] 转录中 (Whisper small)...")
    transcript = transcribe_audio(audio_file)
    print(f"[{name}] 转录完成: {len(transcript)} 字符")

    # 构建笔记
    # 优先用简介（有完整内容），其次用转录
    content = desc if desc and len(desc) > 100 else transcript

    if not content:
        print(f"[FAIL] {name}: 无内容")
        return None

    # 生成 Markdown
    duration = info.get('duration', 0) or today_video.get('length', 0)
    duration_str = f"{duration//60}分{duration%60}秒" if duration else "未知"

    note_content = f"""# AI 早报 {title_date}（{name}）

**来源：** [{title}]({info.get('url', f'https://www.bilibili.com/video/{bvid}')})
**UP主：** {name}
**录制日期：** {title_date}（{['周一','周二','周三','周四','周五','周六','周日'][datetime.strptime(title_date, '%Y-%m-%d').weekday()]}）
**视频时长：** {duration_str}

---

## 今日内容

{content}

---
*由「春笔 ✒️」整理 | {title_date}*
"""

    # 保存
    safe_name = name.replace('/', '_')
    out_file = os.path.join(OUTPUT_DIR, f"{title_date} AI早报-{safe_name}.md")
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(note_content)

    print(f"[OK] {name}: 已保存 → {out_file}")
    return out_file

def main():
    today = date.today().strftime('%Y-%m-%d')
    print(f"Video News Workflow - 多UP主版 | 目标日期: {today}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    results = {}
    for up in UP_LIST:
        try:
            result = process_up(up, today)
            if result:
                results[up['name']] = result
        except Exception as e:
            print(f"[ERROR] {up['name']}: {e}")

    print(f"\n{'='*50}")
    print(f"完成！共处理 {len(results)} 个UP主")
    for name, path in results.items():
        print(f"  - {name}: {path}")

if __name__ == '__main__':
    main()
