#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video News Workflow - 全自动版 (Step 1-5)
获取视频 → 下载音频 → Whisper 转录 → MiniMax AI 整理 → Obsidian 笔记
"""

import sys
import os
import re
import json
import ssl
import subprocess
import requests
from datetime import datetime, date

# 强制 UTF-8 输出
sys.stdout.reconfigure(encoding='utf-8')

# ======================= 配置 =======================
UP_NAME = "橘郡Juya"
UP_UID = "285286947"
VAULT_PATH = r"C:\Users\chenz\Documents\Obsidian Vault"
OUTPUT_DIR = os.path.join(VAULT_PATH, "实时快报")
TEMP_DIR = r"F:\工作区间\ai_news_temp"
FFMPEG_BIN = r"F:\依赖\ffmpeg\ffmpeg-8.1-essentials_build\bin"
WHISPER_VENV = r"F:\skill\faster-whisper-skill\.venv"
MINIMAX_API_KEY = "sk-cp-VmUpM6ECqaSgr33MzjKMQNgy8cFgArOp0CHifxdVi7qsjPUva3I-dmyTkqPreAyS53oSQZzZyCFFLP-bTbgfIXCnaqc7Iv2TJQgsE3fY5ntSxeddnX-XH_o"
BILIBILI_API = f"https://api.bilibili.com/x/space/arc/search?mid={UP_UID}&pn=1&ps=5&order=pubdate"

# ======================= 工具函数 =======================
def run_cmd_raw(cmd, env=None, timeout=120):
    """执行命令，返回 bytes（不做编码假设）"""
    if env is None:
        env = os.environ.copy()
    else:
        env = {**os.environ.copy(), **env}
    # 去掉代理，避免 SSL 问题
    env.pop('HTTP_PROXY', None)
    env.pop('HTTPS_PROXY', None)
    env.pop('http_proxy', None)
    env.pop('https_proxy', None)
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=False,
        env=env, timeout=timeout
    )
    return result

def decode_output(raw_bytes):
    """智能解码 yt-dlp 输出（尝试 UTF-8，失败则 GBK）"""
    if not raw_bytes:
        return ""
    try:
        return raw_bytes.decode('utf-8')
    except UnicodeDecodeError:
        try:
            return raw_bytes.decode('gbk')
        except Exception:
            return raw_bytes.decode('utf-8', errors='replace')

def run_cmd(cmd, env=None, timeout=120):
    """执行命令，返回智能解码的文本"""
    result = run_cmd_raw(cmd, env=env, timeout=timeout)
    return decode_output(result.stdout), decode_output(result.stderr), result.returncode

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def detect_date_from_title(title):
    m = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', title)
    return m.group(1).replace('/', '-') if m else None

# ======================= Step 1: 获取视频 =======================
def step1():
    print("[Step 1] 获取视频...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://space.bilibili.com/"
    }
    videos = []

    # 尝试 Bilibili API
    try:
        resp = requests.get(BILIBILI_API, headers=headers, timeout=15)
        data = resp.json()
        if data["code"] == 0:
            for v in data["data"]["list"]["vlist"]:
                videos.append({
                    "bvid": v["bvid"],
                    "title": v["title"],
                    "pub_date": datetime.fromtimestamp(v["created"]).strftime("%Y-%m-%d"),
                    "title_date": detect_date_from_title(v["title"]),
                    "url": f"https://www.bilibili.com/video/{v['bvid']}"
                })
            print(f"  API 成功: {len(videos)} 个视频")
    except Exception as e:
        print(f"  API 失败: {e}")

    # Fallback: 直接查已知 BV
    if not videos:
        print("  使用直接 BV 查询 fallback...")
        known_bvs = ['BV1aVDPBoEiF', 'BV1oY9NBCEjR', 'BV1cf9WBzE7q', 'BV1ya9VBjEUC']
        for bv in known_bvs:
            stdout, stderr, rc = run_cmd(
                f'yt-dlp --print "%(upload_date)s|%(title)s" "https://www.bilibili.com/video/{bv}"',
                timeout=20
            )
            if rc == 0 and '|' in stdout:
                parts = stdout.strip().split('|', 1)
                if len(parts) == 2:
                    raw_date = parts[0]
                    pub_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
                    title = parts[1]
                    videos.append({
                        "bvid": bv, "title": title,
                        "pub_date": pub_date,
                        "title_date": detect_date_from_title(title),
                        "url": f"https://www.bilibili.com/video/{bv}"
                    })
        print(f"  Fallback 获取 {len(videos)} 个视频")

    # 选择当天视频
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    for v in videos:
        if v["title_date"] == today_str:
            print(f"  [OK] 选中: {v['title'][:40]} (标题日期匹配)")
            return v, None

    v = videos[0] if videos else None
    if v:
        print(f"  [WARN] 今天无匹配，使用最新: {v['title'][:40]}")
        return v, f"[WARN] 使用最新视频 (pub={v['pub_date']})"
    print("[ERROR] 未找到视频")
    return None, None

# ======================= Step 2: 下载音频 =======================
def step2(video_url):
    print(f"\n[Step 2] 下载音频...")
    audio_file = os.path.join(TEMP_DIR, "audio.m4a")
    env = os.environ.copy()
    env["PATH"] = FFMPEG_BIN + ";" + env.get("PATH", "")
    env.pop('HTTP_PROXY', None)
    env.pop('HTTPS_PROXY', None)

    for attempt in range(3):
        stdout, stderr, rc = run_cmd(
            f'yt-dlp -f bestaudio -o "{audio_file}" "{video_url}"',
            env=env, timeout=180
        )
        if rc == 0:
            size = os.path.getsize(audio_file) / 1024 / 1024
            print(f"  [OK] {size:.1f} MB")
            return audio_file
        print(f"  [RETRY {attempt+1}/3]")
    print("[ERROR] 下载失败")
    return None

# ======================= Step 3: 转录 =======================
def step3(audio_file):
    print("\n[Step 3] 转录 (small 模型)...")
    script = os.path.join(TEMP_DIR, "_t.py")
    content = (
        'import sys; '
        'sys.stdout.reconfigure(encoding="utf-8"); '
        'import os; os.environ["HF_ENDPOINT"]="https://hf-mirror.com"; '
        'from faster_whisper import WhisperModel; '
        'm = WhisperModel(r"F:\\\\AI\\\\whisper_models\\\\faster-whisper-small", device="cpu", compute_type="int8"); '
        's, _ = m.transcribe(r"' + audio_file.replace('\\', '\\\\') + '", language="zh", beam_size=5); '
        'print("\\n".join(x.text.strip() for x in s), flush=True)'
    )
    write_file(script, content)

    env = os.environ.copy()
    env['HF_ENDPOINT'] = 'https://hf-mirror.com'
    venv_python = os.path.join(WHISPER_VENV, "Scripts", "python.exe")
    stdout, stderr, rc = run_cmd(f'"{venv_python}" "{script}"', env=env, timeout=600)

    if rc != 0:
        print(f"  [ERROR] {stderr[:200]}")
        return None
    result = stdout.strip()
    print(f"  [OK] {len(result)} 字符")
    return result

# ======================= Step 4: AI 整理 =======================
def step4(transcript):
    print("\n[Step 4] MiniMax AI 整理...")

    prompt = f"""将以下AI早报转录整理成JSON。只输出JSON，无其他内容。
格式：
{{
  "highlights": ["要点1", "要点2", ...],
  "details": [
    {{"title": "标题", "content": "完整句子描述，分2-4点。"}}
  ],
  "corrections": {{"错误": "正确", ...}}
}}
转录：
{transcript}"""

    payload = {
        'model': 'MiniMax-M2.7',
        'messages': [
            {'role': 'system', 'content': '你是AI新闻整理助手，将转录整理成JSON。'},
            {'role': 'user', 'content': prompt}
        ],
        'max_tokens': 2500,
        'temperature': 0.3
    }

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    import urllib.request
    req = urllib.request.Request(
        'https://api.minimax.chat/v1/chat/completions',
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {MINIMAX_API_KEY}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )

    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
        result = json.loads(resp.read().decode('utf-8'))

    raw = result['choices'][0]['message']['content']
    # 去掉 <think>...</think> 标签
    content = re.sub(r'</think>\s*', '', raw.replace('<think>', '')).strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        m = re.search(r'\{[\s\S]*\}', content)
        data = json.loads(m.group()) if m else {}

    highlights = data.get('highlights', [])
    print(f"  [OK] 提取 {len(highlights)} 条要点")
    return data

# ======================= Step 5: 生成笔记 =======================
def step5(video, structured):
    print("\n[Step 5] 生成笔记...")

    highlights = structured.get('highlights', [])
    details = structured.get('details', [])

    detail_md = ""
    for i, item in enumerate(details, 1):
        detail_md += f"### {i}. {item.get('title', '未知')}\n\n{item.get('content', '')}\n\n"

    highlights_md = "\n".join(f"{i+1}. {h}" for i, h in enumerate(highlights))

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
| 时长 | 约4分35秒 |
| BV ID | {video['bvid']} |
| UP主 | {UP_NAME} |

---

## 今日要点

{highlights_md}

---

## 详细内容

{detail_md}

## 相关链接

- [原视频]({video['url']})
- [UP主主页](https://space.bilibili.com/{UP_UID})

---

*由 OpenClaw 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

    output_file = os.path.join(OUTPUT_DIR, f"{video['pub_date']} AI早报.md")
    write_file(output_file, note)
    print(f"  [OK] {output_file} ({os.path.getsize(output_file)} bytes)")
    return output_file

# ======================= 清理 =======================
def cleanup():
    for f in os.listdir(TEMP_DIR):
        try:
            os.remove(os.path.join(TEMP_DIR, f))
        except Exception:
            pass

# ======================= 主流程 =======================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    print("=" * 55)
    print("  Video News Workflow - 全自动")
    print(f"  目标日期: {today_str}")
    print("=" * 55)

    video, warning = step1()
    if not video:
        exit(1)

    output_file = os.path.join(OUTPUT_DIR, f"{video['pub_date']} AI早报.md")
    if os.path.exists(output_file):
        print(f"\n[SKIP] {os.path.basename(output_file)} 已存在")
        exit(0)

    audio_file = step2(video["url"])
    if not audio_file:
        exit(1)

    transcript = step3(audio_file)
    if not transcript:
        exit(1)

    structured = step4(transcript)
    result_file = step5(video, structured)

    cleanup()

    print()
    print("=" * 55)
    print(f"  完成! {os.path.basename(result_file)}")
    print("=" * 55)

if __name__ == "__main__":
    main()
