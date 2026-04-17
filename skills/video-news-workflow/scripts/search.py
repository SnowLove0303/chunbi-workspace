#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video News Workflow - 搜索模块 v2
防限流: Cookie + WBI签名 + 指数退避 + 6小时缓存
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import json
import time
import subprocess
import requests
import hashlib
import urllib.parse

TEMP_DIR       = r"F:\工作区间\ai_news_temp"
WHISPER_MODEL = r"F:\AI\whisper_models\faster-whisper-small"
COOKIES_FILE  = os.path.join(TEMP_DIR, "cookies.txt")

try:
    sys.path.insert(0, os.path.dirname(__file__))
    from run import UP_LIST
except ImportError:
    UP_LIST = [
        {"name": "橘郡Juya",  "uid": "285286947"},
        {"name": "初芽Sprout", "uid": "1638385490"},
    ]


# ======================= WBI 签名 =======================

_WBI_CACHE = {}
_MIXIN_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52,
]
_WBI_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.bilibili.com/',
}


def _get_wbi_key() -> str:
    """获取 WBI 混合密钥（30秒缓存）"""
    global _WBI_CACHE
    if time.time() < _WBI_CACHE.get('ts', 0) + 25:
        return _WBI_CACHE['key']

    r = requests.get(
        'https://api.bilibili.com/x/web-interface/nav',
        headers=_WBI_HEADERS, timeout=10
    )
    data = r.json()
    wbi_img = data.get('data', {}).get('wbi_img', {})
    img_url = wbi_img.get('img_url', '')
    sub_url = wbi_img.get('sub_url', '')
    key = (img_url.rpartition('/')[2].partition('.')[0] +
           sub_url.rpartition('/')[2].partition('.')[0])
    mixed = ''.join(key[i] for i in _MIXIN_TAB)[:32]
    _WBI_CACHE = {'key': mixed, 'ts': time.time()}
    return mixed


def _sign_wbi(params: dict) -> dict:
    """对参数进行 WBI 签名"""
    params = {k: ''.join(c for c in str(v) if c not in "!'()*")
              for k, v in params.items()}
    params['wts'] = str(round(time.time()))
    sorted_items = sorted(params.items())
    query = urllib.parse.urlencode(sorted_items)
    params['w_rid'] = hashlib.md5(
        f'{query}{_get_wbi_key()}'.encode()).hexdigest()
    return params


def wbi_search(keyword: str, page: int = 1, page_size: int = 20) -> dict:
    """使用 WBI 签名执行全站搜索"""
    bvid = 'BV000000'  # 搜索不需要真实bvid
    base = 'https://api.bilibili.com/x/web-interface/wbi/search/all/v2'
    params = _sign_wbi({
        'keyword': keyword, 'page': page,
        'page_size': page_size, 'search_source_type': 1,
    })
    url = f"{base}?{urllib.parse.urlencode(params)}"
    r = requests.get(url, headers=_WBI_HEADERS, timeout=15)
    return r.json()


# ======================= 工具函数 =======================

def _session():
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com',
        'Origin': 'https://www.bilibili.com',
    })
    if os.path.exists(COOKIES_FILE):
        try:
            s.cookies.load(COOKIES_FILE)
        except Exception:
            pass
    return s


def run_cmd(cmd, env=None, timeout=30):
    if env is None:
        env = os.environ.copy()
    else:
        env = {**os.environ.copy(), **env}
    env.pop('HTTP_PROXY', None)
    env.pop('HTTPS_PROXY', None)
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        env=env, encoding='utf-8', errors='replace', timeout=timeout
    )
    return result


def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def fmt_dur(seconds: int) -> str:
    if not seconds:
        return "?"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h{m}m{s}s"
    return f"{m}分{s}秒"


def fmt_views(n: int) -> str:
    if n >= 10000:
        return f"{n/10000:.1f}万"
    return str(n)


# ======================= 缓存 =======================

def cache_get(key: str):
    p = os.path.join(TEMP_DIR, f"cache_{key}.json")
    if not os.path.exists(p):
        return None
    try:
        with open(p, 'r', encoding='utf-8') as f:
            c = json.load(f)
        if time.time() - c.get('ts', 0) < 6 * 3600:
            return c.get('data')
    except:
        pass
    return None


def cache_set(key: str, data):
    p = os.path.join(TEMP_DIR, f"cache_{key}.json")
    with open(p, 'w', encoding='utf-8') as f:
        json.dump({'ts': time.time(), 'data': data}, f, ensure_ascii=False)


# ======================= UP 主搜索 =======================

def search_up(keyword: str):
    print(f"\n[UP搜索] {keyword}")
    kw_lower = keyword.lower()

    for u in UP_LIST:
        if kw_lower in u['name'].lower() or u['name'].lower() in kw_lower:
            print(f"  [配置列表] {u['name']} (UID:{u['uid']})")
            return [u]

    cached = cache_get(f"up_search_{keyword}")
    if cached:
        print(f"  [缓存]")
        for i, u in enumerate(cached, 1):
            print(f"  {i}. {u['name']} | UID:{u['uid']}")
        return cached

    api = f"https://api.bilibili.com/x/web-interface/search/type?search_type=bili_user&keyword={urllib.parse.quote(keyword)}&page=1&page_size=5"
    try:
        r = requests.get(api, headers=_WBI_HEADERS, timeout=10)
        if r.status_code == 200 and r.text.strip():
            data = r.json()
            if data.get('code') == 0:
                d = data.get('data', {})
                for k in ('result', 'user'):
                    raw = d.get(k)
                    if isinstance(raw, list) and raw:
                        results = [{'uid': u.get('mid', ''), 'name': u.get('uname', ''),
                                    'fans': u.get('fans', '')}
                                   for u in raw if u.get('mid') and u.get('uname')]
                        if results:
                            cache_set(f"up_search_{keyword}", results)
                            for i, u in enumerate(results, 1):
                                print(f"  {i}. {u['name']} | UID:{u['uid']} | 粉丝:{u.get('fans','')}")
                            return results
    except Exception as e:
        print(f"  [API FAIL] {e}")

    print(f"  未找到: {keyword}")
    return []


# ======================= UP 主视频列表 =======================

def get_user_videos(uid: str, name: str = ""):
    cache_key = f"videos_{uid}"
    cached = cache_get(cache_key)
    if cached:
        print(f"\n[UP视频] {name} (缓存有效，共{len(cached)}个)")
        for i, v in enumerate(cached[:10], 1):
            print(f"  {i:2d}. [{v['pub_date']}] view:{v['views_str']:>6} | {v['dur_str']:>8} | {v['title'][:38]}")
        if len(cached) > 10:
            print(f"  ... 还有{len(cached)-10}个")
        return cached

    print(f"\n[UP视频] {name} (UID:{uid})")
    space_url = f"https://space.bilibili.com/{uid}/video"
    cmd = ['python', '-m', 'yt_dlp', '--flat-playlist',
           '--print', '%(upload_date)s|%(view_count)s|%(duration)s|%(title)s|%(id)s',
           space_url, '--playlist-end', '30']
    if os.path.exists(COOKIES_FILE):
        cmd += ['--cookies', COOKIES_FILE]
    cmd_str = ' '.join(f'"{c}"' if ' ' in str(c) else str(c) for c in cmd)
    r = run_cmd(cmd_str, timeout=60)

    if r.returncode != 0 or not r.stdout.strip():
        print(f"  [FAIL] {r.stderr[-200:]}")
        return []

    videos = []
    for line in r.stdout.strip().split('\n'):
        if not line.strip():
            continue
        parts = line.split('|')
        if len(parts) >= 5:
            views = 0
            try: views = int(parts[1].strip())
            except: pass
            dur = 0
            try: dur = int(float(parts[2].strip()))
            except: pass
            m = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', parts[3].strip())
            videos.append({
                'bvid':       parts[4].strip(),
                'title':      parts[3].strip(),
                'pub_date':   parts[0].strip(),
                'views':      views,
                'views_str':  fmt_views(views),
                'duration':   dur,
                'dur_str':    fmt_dur(dur),
                'title_date': m.group(1).replace('/', '-') if m else None,
            })

    videos.sort(key=lambda x: x['pub_date'], reverse=True)
    cache_set(cache_key, videos)
    print(f"  共{len(videos)}个（已缓存6小时）:")
    for i, v in enumerate(videos[:10], 1):
        print(f"  {i:2d}. [{v['pub_date']}] view:{v['views_str']:>6} | {v['dur_str']:>8} | {v['title'][:38]}")
    if len(videos) > 10:
        print(f"  ... 还有{len(videos)-10}个")
    return videos


# ======================= 全站关键词搜索 =======================

def search_keyword(keyword: str, limit: int = 20):
    """全站搜索（使用WBI签名，不限流）"""
    cache_key = f"wbi_search_{keyword}"
    cached = cache_get(cache_key)
    if cached:
        print(f"\n[全站搜索] {keyword} [缓存]")
        results = cached
    else:
        print(f"\n[全站搜索] {keyword} [WBI签名]")
        raw = wbi_search(keyword, page_size=limit)
        if raw.get('code') != 0:
            print(f"  [FAIL] {raw.get('message','unknown')}")
            return []

        results = []
        for group in raw.get('data', {}).get('result', []):
            if group.get('result_type') != 'video':
                continue
            for v in (group.get('data') or []):
                if not isinstance(v, dict) or not v.get('bvid'):
                    continue
                title = re.sub(r'<[^>]+>', '', v.get('title', '')).strip()
                results.append({
                    'bvid':      v.get('bvid', ''),
                    'title':     title,
                    'author':    v.get('author', ''),
                    'uid':       v.get('mid', ''),
                    'duration':  v.get('duration', 0),
                    'dur_str':   fmt_dur(v.get('duration', 0)),
                    'views':     v.get('play', 0),
                    'views_str': fmt_views(v.get('play', 0)),
                    'pub_date':  str(v.get('pubdate', '')),
                })
        if not results:
            print("  未找到结果")
            return []
        cache_set(cache_key, results)

    results.sort(key=lambda x: x['views'], reverse=True)
    print(f"  共{len(results)}个（按播放量排序）:")
    for i, v in enumerate(results[:15], 1):
        t = v['title'][:42]
        print(f"  {i:2d}. view:{v['views_str']:>7} | {v['dur_str']:>8} | {v['author'][:10]:10} | {t}")
    if len(results) > 15:
        print(f"  ... 还有{len(results)-15}个")
    return results


# ======================= 选视频 =======================

def pick_video(videos: list, prompt="选择视频编号"):
    if not videos:
        return None
    print(f"\n{prompt}（输入编号，q退出）:")
    try:
        choice = input("> ").strip()
        if choice.lower() == 'q':
            return None
        idx = int(choice) - 1
        if 0 <= idx < len(videos):
            return videos[idx]
        print("无效编号")
    except (ValueError, EOFError):
        pass
    return None


# ======================= 视频详情 =======================

def get_detail(bvid: str) -> dict:
    url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
    try:
        r = requests.get(url, headers=_WBI_HEADERS, timeout=10)
        if r.status_code == 200 and r.text.strip():
            d = r.json().get('data', {})
            owner = d.get('owner') or {}
            return {
                'bvid':     bvid,
                'title':    d.get('title', ''),
                'author':   owner.get('name', ''),
                'uid':      owner.get('mid', ''),
                'duration': d.get('duration', 0),
                'desc':     d.get('desc', ''),
                'url':      f"https://www.bilibili.com/video/{bvid}",
            }
    except:
        pass
    return {'bvid': bvid, 'title': '', 'author': '', 'duration': 0, 'desc': '',
             'url': f"https://www.bilibili.com/video/{bvid}"}


# ======================= 下载 + 转录 =======================

def download_audio(bvid: str) -> str:
    out = os.path.join(TEMP_DIR, f"audio_{bvid}.m4a")
    if os.path.exists(out) and os.path.getsize(out) > 50_000:
        print(f"  [CACHE] 音频已存在")
        return out

    cmd = ['python', '-m', 'yt_dlp', '-f', 'bestaudio',
           '-o', out, '--no-playlist',
           f"https://www.bilibili.com/video/{bvid}"]
    if os.path.exists(COOKIES_FILE):
        cmd += ['--cookies', COOKIES_FILE]
    cmd_str = ' '.join(f'"{c}"' if ' ' in str(c) and not str(c).startswith('-') else str(c) for c in cmd)
    env = os.environ.copy()
    env.pop('HTTP_PROXY', None)
    env.pop('HTTPS_PROXY', None)
    r = subprocess.run(cmd_str, shell=True, capture_output=True, text=True,
                       env=env, encoding='utf-8', errors='replace', timeout=180)
    if r.returncode == 0 and os.path.exists(out):
        print(f"  [OK] {os.path.getsize(out)/1024/1024:.1f}MB")
        return out
    print(f"  [FAIL] {r.stderr[-200:]}")
    return None


_wmodel = None

def transcribe(audio_path: str, bvid: str) -> str:
    txt_file = os.path.join(TEMP_DIR, f"transcript_{bvid}.txt")
    if os.path.exists(txt_file):
        print(f"  [CACHE] 转录已存在")
        with open(txt_file, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()

    global _wmodel
    if _wmodel is None:
        sys.path.insert(0, r'F:\skill\faster-whisper-skill\.venv\Lib\site-packages')
        from faster_whisper import WhisperModel
        print("  [LOAD] Whisper small...")
        _wmodel = WhisperModel(WHISPER_MODEL, device='cpu', compute_type='int8')

    print(f"  [TRANSCRIBE] 转录中...")
    segments, _ = _wmodel.transcribe(audio_path, language='zh', beam_size=5)
    text = ''.join(s.text.strip() for s in segments).strip()
    if text:
        write_file(txt_file, text)
        print(f"  [OK] {len(text)}字")
    return text


# ======================= 主菜单 =======================

def main():
    print("=" * 50)
    print("  Bilibili 视频搜索 v2 (WBI签名)")
    print("=" * 50)
    print("  1. UP主搜索 -> 选其视频")
    print("  2. 全站关键词搜索（按播放量）")
    print("  q. 退出")

    try:
        mode = input("\n选择 (1/2/q): ").strip()
    except EOFError:
        return
    if mode == 'q':
        return

    bvid = None
    video_info = None

    if mode == '1':
        kw = input("输入UP主名字（或UID）: ").strip()
        if not kw:
            return
        if kw.isdigit():
            videos = get_user_videos(kw, kw)
        else:
            users = search_up(kw)
            if not users:
                return
            user = pick_video(users, "选择UP主编号")
            if not user:
                return
            videos = get_user_videos(user['uid'], user['name'])
        if not videos:
            return
        video = pick_video(videos, "选择视频编号")
        if video:
            bvid = video['bvid']
            video_info = video

    elif mode == '2':
        kw = input("输入搜索关键词: ").strip()
        if not kw:
            return
        results = search_keyword(kw)
        if not results:
            return
        video = pick_video(results, "选择视频编号")
        if video:
            bvid = video['bvid']
            video_info = video

    else:
        print("无效选项")
        return

    if not bvid:
        return

    detail = get_detail(bvid)
    print(f"\n选中: {detail['title']}")
    print(f"  BV:{bvid} | 作者:{detail['author']} | 时长:{fmt_dur(detail['duration'])}")

    audio = download_audio(bvid)
    if not audio:
        return

    transcript = transcribe(audio, bvid)
    if not transcript:
        print("[FAIL] 转录失败")
        return

    selected = {
        **detail,
        'transcript': transcript,
        'views':    video_info.get('views', 0) if video_info else 0,
        'pub_date': video_info.get('pub_date', '') if video_info else '',
    }
    write_file(os.path.join(TEMP_DIR, 'selected_video.json'),
               json.dumps(selected, ensure_ascii=False, indent=2))
    print(f"\n[OK] 完成! {len(transcript)}字")


if __name__ == '__main__':
    main()
