#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video News Workflow - 视频转笔记自动化（完整版）
获取视频 → 转录 → AI 结构化 → 生成 Obsidian 笔记
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import json
import subprocess
import requests
from datetime import datetime, date

# ======================= 配置 =======================
UP_NAME = "橘郡Juya"
UP_UID = "285286947"
VAULT_PATH = r"C:\Users\chenz\Documents\Obsidian Vault"
OUTPUT_DIR = os.path.join(VAULT_PATH, "实时快报")
TEMP_DIR = r"F:\工作区间\ai_news_temp"
FFMPEG_BIN = r"F:\依赖\ffmpeg\ffmpeg-8.1-essentials_build\bin"
WHISPER_VENV = r"F:\skill\faster-whisper-skill\.venv"
BILIBILI_API = f"https://api.bilibili.com/x/space/arc/search?mid={UP_UID}&pn=1&ps=5&order=pubdate"

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
    """从标题提取日期，如 'AI 早报 2026-04-04' → '2026-04-04'"""
    m = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', title)
    if m:
        return m.group(1).replace('/', '-')
    return None

def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

# ======================= Step 1: 获取视频 =======================
def fetch_latest_videos():
    print("[Step 1] Fetching videos from Bilibili API...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://space.bilibili.com/"
    }
    try:
        resp = requests.get(BILIBILI_API, headers=headers, timeout=15)
        data = resp.json()
        if data["code"] != 0:
            raise Exception(f"API error: {data.get('message')}")
        videos = []
        for v in data["data"]["list"]["vlist"]:
            title_date = detect_date_from_title(v["title"])
            pub_date = datetime.fromtimestamp(v["created"]).strftime("%Y-%m-%d")
            videos.append({
                "bvid": v["bvid"],
                "title": v["title"],
                "pub_date": pub_date,
                "title_date": title_date,
                "url": f"https://www.bilibili.com/video/{v['bvid']}"
            })
        print(f"  Found {len(videos)} videos")
        for v in videos[:3]:
            print(f"  [{v['pub_date']}] {v['title_date'] or '?'} | {v['bvid']} | {v['title'][:40]}")
        return videos
    except Exception as e:
        print(f"  [WARN] API failed: {e}")
        print("  [FALLBACK] Using yt-dlp...")
        return fetch_via_ytdlp()

def fetch_via_ytdlp():
    """用 yt-dlp 遍历最近视频获取信息，失败时返回空列表"""
    env = os.environ.copy()
    env.pop('HTTP_PROXY', None)
    env.pop('HTTPS_PROXY', None)
    
    # 方式1: 尝试 yt-dlp --playlist-end 方式获取空间视频
    r = run_cmd(
        f'yt-dlp --flat-playlist --print "%(upload_date)s|%(title)s|%(id)s" '
        f'"https://space.bilibili.com/{UP_UID}/uploaded?pn=1&ps=5" --playlist-end 5',
        env=env, timeout=30
    )
    if r.returncode == 0 and r.stdout.strip():
        videos = []
        for line in r.stdout.strip().split('\n'):
            parts = line.split('|')
            if len(parts) >= 3:
                videos.append({
                    "bvid": parts[2], "title": parts[1],
                    "pub_date": parts[0],
                    "title_date": detect_date_from_title(parts[1]),
                    "url": f"https://www.bilibili.com/video/{parts[2]}"
                })
        if videos:
            return videos
    
    # 方式2: 查最近的已知视频（BV1aVDPBoEiF 等）
    # 从最新往回查，用 yt-dlp 单独查每个 BV 的信息
    known_bvs = ['BV1aVDPBoEiF', 'BV1oY9NBCEjR', 'BV1cf9WBzE7q', 'BV1ya9VBjEUC']
    videos = []
    for bv in known_bvs:
        r = run_cmd(
            f'yt-dlp --print "%(upload_date)s|%(title)s" '
            f'"https://www.bilibili.com/video/{bv}"',
            env=env, timeout=20
        )
        if r.returncode == 0 and r.stdout.strip():
            parts = r.stdout.strip().split('|', 1)
            if len(parts) == 2:
                pub_date, title = parts
                videos.append({
                    "bvid": bv, "title": title,
                    "pub_date": pub_date,
                    "title_date": detect_date_from_title(title),
                    "url": f"https://www.bilibili.com/video/{bv}"
                })
    
    if videos:
        print(f"  [FALLBACK] Got {len(videos)} videos via direct BV check")
    else:
        print(f"  [ERROR] All fallbacks failed")
    return videos

def select_video(videos, target_date: date):
    today_str = target_date.strftime("%Y-%m-%d")
    for v in videos:
        if v["title_date"] == today_str:
            print(f"  [OK] Title date matches {today_str}: {v['title'][:50]}")
            return v, None
    for v in videos:
        if v["pub_date"] == today_str:
            print(f"  [OK] Pubdate matches {today_str}: {v['title'][:50]}")
            return v, f"[WARN] Using pubdate match: {v['title'][:50]}"
    v = videos[0]
    print(f"  [WARN] No video for {today_str}, using latest: {v['title'][:50]}")
    msg = f"[WARN] Using '{v['title']}' (pub={v['pub_date']}, title_date={v['title_date']})"
    return v, msg

# ======================= Step 2: 下载音频 =======================
def download_audio(video_url, audio_path):
    print(f"\n[Step 2] Downloading audio...")
    env = os.environ.copy()
    env["PATH"] = FFMPEG_BIN + ";" + env.get("PATH", "")
    env.pop('HTTP_PROXY', None)
    env.pop('HTTPS_PROXY', None)
    for attempt in range(3):
        r = run_cmd(
            f'yt-dlp -f bestaudio -o "{audio_path}" "{video_url}"',
            env=env, timeout=180
        )
        if r.returncode == 0:
            size_mb = os.path.getsize(audio_path) / 1024 / 1024
            print(f"  [OK] Audio: {size_mb:.1f} MB")
            return True
        print(f"  [RETRY {attempt+1}/3] {r.stderr[:150]}")
    return False

# ======================= Step 3: 转录 =======================
def transcribe(audio_path, transcript_path):
    print("\n[Step 3] Transcribing (small model)...")
    venv_python = os.path.join(WHISPER_VENV, "Scripts", "python.exe")
    env = os.environ.copy()
    env['HF_ENDPOINT'] = 'https://hf-mirror.com'
    
    # 写入临时转录脚本
    transcribe_script = os.path.join(TEMP_DIR, "_transcribe.py")
    script_content = f'''
import sys
sys.stdout.reconfigure(encoding="utf-8")
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
from faster_whisper import WhisperModel
model = WhisperModel(r"F:\\AI\\whisper_models\\faster-whisper-small", device="cpu", compute_type="int8")
segments, info = model.transcribe(r"{audio_path}", language="zh", beam_size=5)
lines = [seg.text.strip() for seg in segments]
result = chr(10).join(lines)
print(result, flush=True)
'''
    write_file(transcribe_script, script_content)
    
    r = run_cmd(f'"{venv_python}" "{transcribe_script}"', env=env, timeout=600)
    if r.returncode != 0:
        print(f"  [ERROR] {r.stderr[:300]}")
        return None
    result = r.stdout.strip()
    write_file(transcript_path, result)
    print(f"  [OK] Transcript: {len(result)} chars")
    return result

# ======================= Step 4: AI 结构化 =======================
def structure_with_ai(transcript):
    """调用 OpenClaw 子 agent 对转录文本进行结构化"""
    print("\n[Step 4] AI structuring...")
    
    # 写入临时文件供子 agent 读取
    raw_path = os.path.join(TEMP_DIR, "raw_transcript.txt")
    structured_path = os.path.join(TEMP_DIR, "structured.json")
    write_file(raw_path, transcript)
    
    prompt = f"""你是一个AI新闻整理助手。下面是一段AI早报的原始转录文本，请将其整理成结构化的中文Markdown笔记。

## 转录文本
{transcript}

## 输出要求

请生成以下格式的JSON（注意是JSON，key为英文）：
{{
  "video_info": {{
    "duration": "约X分X秒",
    "bv_id": "BV号",
    "up_name": "UP主名"
  }},
  "highlights": ["要点1", "要点2", ...],  // 3-8条今日核心新闻
  "details": [
    {{
      "title": "新闻标题",
      "content": "详细描述，分2-4点说明"
    }},
    ...
  ],
  "corrections": {{
    "wrong": "正确",
    ...
  }}
}}

## 格式规则
- highlights最多8条，每条不超过30字
- details中的content用中文句号分隔的完整句子，去除所有语气词和重复
- corrections用于修正Whisper转录错误的名词（如"阿里通益"→"阿里通义"），可为空对象
- 输出只包含JSON，不要有markdown代码块包裹
"""
    
    # 写入 task 文件
    task_file = os.path.join(TEMP_DIR, "structure_task.txt")
    write_file(task_file, prompt)
    
    print("  [INFO] 子agent处理中，读取结果...")
    return structured_path, raw_path

# ======================= Step 5: 生成笔记 =======================
def generate_note(video, structured_data, corrections, output_path):
    print("\n[Step 5] Generating note...")
    
    # 应用纠错
    transcript_corrected = structured_data.get("raw_transcript", "")
    
    duration = structured_data.get("video_info", {}).get("duration", "未知")
    highlights = structured_data.get("highlights", [])
    details = structured_data.get("details", [])
    
    # 构建详细条目Markdown
    detail_sections = []
    for i, item in enumerate(details, 1):
        title = item.get("title", "未知")
        content = item.get("content", "")
        detail_sections.append(f"### {i}. {title}\n\n{content}\n")
    
    highlights_md = "\n".join(f"{i+1}. {h}" for i, h in enumerate(highlights))
    details_md = "\n\n".join(detail_sections)
    
    note = f"""---
date: {video['pub_date']}
source: Bilibili
up: {UP_NAME}
video: {video['title']}
url: {video['url']}
tags:
  - AI早报
  - 实时快报
---

# {video['title']}

> 日期: {video['pub_date']}
> UP主: {UP_NAME}
> 原始视频: [{video['title']}]({video['url']})

---

## 视频信息

| 属性 | 值 |
|------|-----|
| 时长 | {duration} |
| BV ID | {video['bvid']} |
| UP主 | {UP_NAME} |

---

## 今日要点

{highlights_md}

---

## 详细内容

{details_md}

---

## 相关链接

- [原视频]({video['url']})
- [UP主主页](https://space.bilibili.com/{UP_UID})

---

*由 OpenClaw 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    
    write_file(output_path, note)
    size = os.path.getsize(output_path)
    print(f"  [OK] Note saved: {output_path} ({size} bytes)")

# ======================= 主流程 =======================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    
    print("=" * 55)
    print("  Video News Workflow - Daily AI News (Full)")
    print(f"  Target date: {today_str}")
    print("=" * 55)
    
    # Step 1: 获取视频
    videos = fetch_latest_videos()
    if not videos:
        print("[ERROR] No videos found")
        exit(1)
    
    video, warning = select_video(videos, today)
    video_date = video["pub_date"]
    
    # 检查已处理
    output_file = os.path.join(OUTPUT_DIR, f"{video_date} AI早报.md")
    if os.path.exists(output_file):
        print(f"\n[SKIP] {output_file} already exists!")
        exit(0)
    
    # Step 2: 下载音频
    audio_file = os.path.join(TEMP_DIR, "audio.m4a")
    if not download_audio(video["url"], audio_file):
        exit(1)
    
    # Step 3: 转录
    transcript_file = os.path.join(TEMP_DIR, "transcript.txt")
    transcript = transcribe(audio_file, transcript_file)
    
    if not transcript.strip():
        print("[ERROR] Empty transcript")
        exit(1)
    
    # Step 4: AI 结构化 - 通过子 agent
    structured_path, raw_path = structure_with_ai(transcript)
    
    # 读取子agent生成的结构化数据
    # （子agent会写入 structured_path，这里由父进程读取）
    # 实际调用由 OpenClaw 主会话完成，见下方说明
    
    # 打印提示，供主会话处理
    print()
    print("=" * 55)
    print("  Transcript ready. Awaiting AI structuring via main session...")
    print("=" * 55)
    
    # 将关键信息写入状态文件，供主会话读取
    state = {
        "video": video,
        "transcript": transcript,
        "transcript_file": transcript_file,
        "structured_path": structured_path,
        "raw_path": raw_path,
        "output_file": output_file,
        "warning": warning
    }
    state_file = os.path.join(TEMP_DIR, "workflow_state.json")
    write_file(state_file, json.dumps(state, ensure_ascii=False, indent=2))
    print(f"  State saved to: {state_file}")

if __name__ == "__main__":
    main()
