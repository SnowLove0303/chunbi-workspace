# -*- coding: utf-8 -*-
"""OpenCLI Bilibili 命令封装"""
import subprocess
import json
import sys
import re
import os
import shlex

# opencli 命令路径
OPENCLI_CMD = r"C:\Users\chenz\AppData\Roaming\npm\opencli.cmd"

def run(args: list[str], timeout=60) -> dict:
    """执行 opencli bilibili 命令，返回 JSON 结果"""
    cmd = [OPENCLI_CMD] + args
    env = os.environ.copy()
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout,
        encoding='utf-8', errors='replace', env=env
    )
    # 直接解析完整 stdout 为 JSON
    try:
        return json.loads(result.stdout.strip())
    except Exception:
        pass
    return {"_raw": result.stdout, "_stderr": result.stderr, "_returncode": result.returncode}

def search_videos(query: str, limit=20, page=1) -> list[dict]:
    """搜索视频"""
    args = [
        "bilibili", "search", query,
        "--type", "video",
        "--limit", str(limit),
        "--page", str(page),
        "--format", "json"
    ]
    data = run(args)
    if isinstance(data, list):
        return data
    return []

def get_user_videos(uid: str, limit=20, page=1, order="pubdate") -> list[dict]:
    """获取 UP 主视频列表"""
    args = [
        "bilibili", "user-videos", uid,
        "--limit", str(limit),
        "--page", str(page),
        "--order", order,
        "--format", "json"
    ]
    data = run(args)
    if isinstance(data, list):
        return data
    return []

def download_video(bvid: str, output_dir: str, quality="best") -> dict:
    """下载视频"""
    args = [
        "bilibili", "download", bvid,
        "--output", output_dir,
        "--quality", quality,
        "--format", "json"
    ]
    data = run(args, timeout=300)
    return data

def get_subtitle(bvid: str, lang="zh-CN") -> list[dict]:
    """获取字幕"""
    args = [
        "bilibili", "subtitle", bvid,
        "--lang", lang,
        "--format", "json"
    ]
    data = run(args)
    if isinstance(data, list):
        return data
    return []

def extract_bvid(url_or_bvid: str) -> str:
    """从 URL 或 BV 号提取 BV"""
    if url_or_bvid.startswith('BV'):
        return url_or_bvid
    m = re.search(r'BV[\w]+', url_or_bvid)
    return m.group(0) if m else url_or_bvid

def normalize_video_info(raw: dict) -> dict:
    """统一不同来源的视频信息格式"""
    # 用户视频列表格式（优先判断，有 plays 字段）
    if 'plays' in raw and 'rank' in raw:
        bvid = extract_bvid(raw.get('url', ''))
        title = raw.get('title', '')
        title = re.sub(r'[\\/:*?"<>|]', '_', title)
        return {
            'bvid': bvid,
            'title': title,
            'author': '',
            'plays': raw.get('plays', 0),
            'date': raw.get('date', ''),
            'url': raw.get('url', ''),
            'source': 'user'
        }
    # 搜索结果格式（有 author 字段）
    if 'url' in raw and 'rank' in raw and 'author' in raw:
        bvid = extract_bvid(raw.get('url', ''))
        title = raw.get('title', '')
        title = re.sub(r'[\\/:*?"<>|]', '_', title)
        return {
            'bvid': bvid,
            'title': title,
            'author': raw.get('author', ''),
            'score': raw.get('score', 0),
            'url': raw.get('url', ''),
            'source': 'search'
        }
    return raw

def match_date(videos: list[dict], target_date: str) -> list[dict]:
    """按日期过滤视频"""
    if not target_date:
        return videos
    matched = []
    for v in videos:
        date = v.get('date', '')
        title = v.get('title', '')
        if target_date in date or target_date in title:
            matched.append(v)
    return matched

if __name__ == '__main__':
    # 测试
    print("搜索测试:")
    results = search_videos("AI 大模型 2026", limit=3)
    for r in results:
        print(f"  {normalize_video_info(r)}")
    
    print("\n用户视频列表测试:")
    videos = get_user_videos("285286947", limit=3)
    for v in videos:
        print(f"  {normalize_video_info(v)}")
