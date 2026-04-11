#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Video News Workflow v3 - 优化版
- 多UP主并行处理（橘郡Juya + 初芽Sprout）
- 全部转录（Whisper small + FunASR 备用）
- 结构化格式化（note_formatter.py）
- md_beautifier 美化
- 按日期缓存
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
import json
import time
import subprocess
import requests
from datetime import datetime, date
from typing import Optional

# 禁用代理（避免公司网络干扰B站请求）
for _k in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy'):
    os.environ.pop(_k, None)

_NO_PROXY = {'http': None, 'https': None}

# curl_cffi: 模拟Chrome浏览器指纹，绕过B站反爬
try:
    import curl_cffi
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False


def _curl_get(url, **kwargs):
    """使用curl_cffi模拟Chrome指纹请求，失败时fallback到requests"""
    if CURL_CFFI_AVAILABLE:
        try:
            from curl_cffi.requests import Session as CurlSession
            s = CurlSession(impersonate='chrome', timeout=kwargs.pop('timeout', 10))
            # 禁用代理
            s.trust_env = False
            r = s.get(url, **kwargs)
            return r
        except Exception as e:
            log(f" [WARN] curl_cffi失败，fallback到requests: {e}")
    # fallback
    kwargs.pop('timeout', None)
    return requests.get(url, **kwargs, proxies=_NO_PROXY)

# ======================= 配置 =======================
UP_LIST = [
    {"name": "橘郡Juya", "uid": "285286947"},
    {"name": "初芽Sprout", "uid": "1638385490"},
]

VAULT_PATH = r"C:\Users\chenz\Documents\Obsidian Vault"
OUTPUT_DIR = os.path.join(VAULT_PATH, "实时快报")
TEMP_DIR = r"F:\工作区间\ai_news_temp"
FFMPEG_BIN = r"F:\依赖\ffmpeg\ffmpeg-8.1-essentials_build\bin"

# Whisper 模型（small 已预下载）
WHISPER_MODEL_SMALL = r"F:\AI\whisper_models\faster-whisper-small"
WHISPER_MODEL_MEDIUM = r"F:\AI\whisper_models\faster-whisper-medium"

# ASR 引擎选择: "whisper"(默认) 或 "funasr"
# 设置环境变量 ASR_ENGINE=funasr 可切换
ASR_ENGINE = os.environ.get('ASR_ENGINE', 'whisper').lower()
FUNASR_VENV = r"F:\skill\funasr-skill\.venv"

COOKIES_FILE = os.path.join(TEMP_DIR, "cookies.txt")

# ======================= 工具函数 =======================
def log(msg=''):
    print(msg)

def run_cmd(cmd, env=None, timeout=120):
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
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def read_file(path):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def detect_date(title: str) -> Optional[str]:
    m = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', title)
    return m.group(1).replace('/', '-') if m else None

def cache_get(key: str, target_date: str = None):
    """获取缓存，支持日期过滤"""
    p = os.path.join(TEMP_DIR, f"cache_{key}.json")
    if not os.path.exists(p):
        return None
    try:
        with open(p, 'r', encoding='utf-8') as f:
            c = json.load(f)
        # 日期过滤
        if target_date and c.get('date') != target_date:
            return None
        if time.time() - c.get('ts', 0) < 6 * 3600:
            return c.get('data')
    except:
        pass
    return None

def cache_set(key: str, data, target_date: str = None):
    """设置缓存"""
    p = os.path.join(TEMP_DIR, f"cache_{key}.json")
    with open(p, 'w', encoding='utf-8') as f:
        json.dump({'ts': time.time(), 'date': target_date, 'data': data}, f, ensure_ascii=False)

# ======================= Step 1: 获取视频列表 =======================
def fetch_videos(uid: str, target_date: str = None) -> list:
    """获取UP主视频列表：优先yt-dlp，失败则用B站API"""
    cached = cache_get(f"videos_{uid}", target_date)
    if cached:
        log(f" [CACHE] 视频列表缓存有效")
        return cached

    # 方法1: yt-dlp
    videos = _fetch_videos_ytdlp(uid)
    if videos:
        cache_set(f"videos_{uid}", videos, target_date)
        log(f" [OK] yt-dlp获取{len(videos)}个视频")
        return videos

    # 方法2: B站API直接（备用）
    log(f" [WARN] yt-dlp失败，尝试API...")
    videos = _fetch_videos_api(uid, target_date)
    if videos:
        cache_set(f"videos_{uid}", videos, target_date)
        log(f" [OK] API获取{len(videos)}个视频")
        return videos

    if cached:
        log(f" [CACHE] 使用过期缓存")
        return cached
    log(f" [FAIL] 无法获取视频列表")
    return []


def _fetch_videos_ytdlp(uid: str) -> list:
    """yt-dlp 方式获取视频列表"""
    space_url = f"https://space.bilibili.com/{uid}/video"
    cookies_arg = f'--cookies "{COOKIES_FILE}"' if os.path.exists(COOKIES_FILE) else ''
    r = run_cmd(
        f'yt-dlp --flat-playlist '
        f'--print "%(upload_date)s|%(view_count)s|%(duration)s|%(title)s|%(id)s" '
        f'"{space_url}" --playlist-end 10 {cookies_arg}',
        timeout=60
    )
    if r.returncode != 0 or not r.stdout.strip():
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
            videos.append({
                'bvid': parts[4].strip(),
                'title': parts[3].strip(),
                'pub_date': parts[0].strip(),
                'title_date': detect_date(parts[3].strip()),
                'duration': dur,
                'views': views,
            })
    return videos


def _load_cookies(cookie_file):
    """解析 Netscape 格式 cookies.txt，返回 requests CookieJar"""
    import http.cookiejar
    try:
        cj = http.cookiejar.MozillaCookieJar(cookie_file)
        cj.load(ignore_discard=True, ignore_expires=True)
        return cj
    except Exception:
        return None

def _fetch_videos_api(uid: str, target_date: str = None) -> list:
    """B站API直接获取视频列表（WBI签名版），412时尝试搜索API"""
    from wbi import _sign_wbi, search_with_wbi

    # 方法A: Space API
    url = f"https://api.bilibili.com/x/space/arc/search"
    params = {
        'mid': uid, 'ps': 30, 'pn': 1, 'order': 'pubdate',
        'platform': 'web', 'web_location': '15501001',
    }
    try:
        cookies = _load_cookies(COOKIES_FILE) if os.path.exists(COOKIES_FILE) else None
        params = _sign_wbi(params.copy(), 'BV123456')
        resp = _curl_get(url, params=params,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                     'Referer': 'https://www.bilibili.com/'},
            cookies=cookies)

        if resp.status_code == 412:
            log(f" [WARN] Space API 限流(412)，尝试搜索API...")
            raise Exception("rate_limited")

        text = resp.content.decode('utf-8', errors='replace')
        data = json.loads(text)

        if data.get('code') == -799:
            log(f" [WARN] Space API 返回-799，尝试搜索API...")
            raise Exception("rate_limited")

        if data.get('code') == 0:
            videos = []
            for v in data['data']['list']['vlist']:
                title = v.get('title', '')
                bvid = v.get('bvid', '')
                pubdate = time.strftime('%Y-%m-%d', time.localtime(v.get('pubdate', 0)))
                dur_str = v.get('length', '0:00')
                dur_sec = 0
                parts = dur_str.split(':')
                if len(parts) == 2:
                    try: dur_sec = int(parts[0])*60 + int(parts[1])
                    except: pass
                date_m = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', title)
                videos.append({
                    'bvid': bvid,
                    'title': title,
                    'pub_date': pubdate,
                    'title_date': date_m.group(1).replace('/', '-') if date_m else None,
                    'duration': dur_sec,
                    'views': v.get('comment', 0),
                })
            return videos
    except Exception as e:
        if str(e) == "rate_limited":
            pass  # 继续尝试搜索API
        else:
            log(f" [WARN] Space API失败: {e}")

    # 方法B: Web搜索API备用（无需WBI，直接搜索"AI早报"按UP主过滤）
    try:
        up_name_map = {"285286947": "橘郡Juya", "1638385490": "初芽Sprout"}
        up_name = up_name_map.get(uid, uid)
        search_kw = f"AI早报 {target_date or ''}"
        log(f" [INFO] 搜索API(无WBI): {search_kw}")
        
        search_url = 'https://api.bilibili.com/x/web-interface/search/type'
        params = {
            'search_type': 'video',
            'keyword': search_kw,
            'page': 1,
            'page_size': 30,
            'platform': 'pc',
            'order': 'pubdate',
        }
        resp = _curl_get(search_url, params=params,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                     'Referer': 'https://www.bilibili.com/',
                     'Accept': 'application/json, text/plain, */*',
                     'Accept-Language': 'zh-CN,zh;q=0.9'},
            cookies=cookies)
        result = resp.json()
        
        if result.get('code') == 0:
            videos = []
            for v in result.get('data', {}).get('result', []):
                if not isinstance(v, dict):
                    continue
                author = v.get('author', '') or v.get('uname', '')
                title = v.get('title', '').replace('<em class="keyword">', '').replace('</em>', '')
                bvid = v.get('bvid', '')
                pubdate_ts = v.get('pubdate', 0)
                pubdate = time.strftime('%Y-%m-%d', time.localtime(pubdate_ts)) if pubdate_ts else ''
                dur_str = v.get('duration', '')
                dur_sec = 0
                parts = dur_str.split(':')
                if len(parts) == 2:
                    try: dur_sec = int(parts[0])*60 + int(parts[1])
                    except: pass
                date_m = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', title)
                videos.append({
                    'bvid': bvid,
                    'title': title,
                    'pub_date': pubdate,
                    'title_date': date_m.group(1).replace('/', '-') if date_m else None,
                    'duration': dur_sec,
                    'views': v.get('play', 0),
                    'author': author,
                })
            # 按UP主名过滤
            up_videos = [v for v in videos if up_name in v.get('author', '') or up_name in v.get('title', '')]
            used = up_videos or [v for v in videos if 'AI早报' in v.get('title', '')]
            if used:
                log(f" [OK] 搜索API获取{len(used)}个视频(过滤后)")
                return used[:10]
    except Exception as e2:
        log(f" [WARN] 搜索API失败: {e2}")

    return []

def fetch_video_detail(bvid: str) -> dict:
    """获取视频详细信息"""
    url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
    try:
        r = _curl_get(url, headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://www.bilibili.com/',
        })
        # 尝试UTF-8（大多数API），失败再用GBK
        for enc in ('utf-8', 'gbk', 'gb2312'):
            try:
                text = r.content.decode(enc, errors='strict')
                break
            except:
                continue
        else:
            text = r.content.decode('utf-8', errors='replace')
        data = json.loads(text)
        if data.get('code') == 0:
            d = data['data']
            owner = d.get('owner') or {}
            return {
                'bvid': bvid,
                'title': d.get('title', ''),
                'author': owner.get('name', ''),
                'uid': owner.get('mid', ''),
                'duration': d.get('duration', 0),
                'desc': d.get('desc', ''),
                'url': f"https://www.bilibili.com/video/{bvid}",
            }
    except:
        pass
    return {'bvid': bvid, 'title': '', 'author': '', 'uid': '', 'duration': 0, 'desc': '', 'url': f"https://www.bilibili.com/video/{bvid}"}

# ======================= Step 2: 下载音频 =======================
def download_audio(bvid: str) -> Optional[str]:
    out = os.path.join(TEMP_DIR, f"audio_{bvid}.m4a")
    if os.path.exists(out) and os.path.getsize(out) > 100_000:
        log(f" [CACHE] 音频已存在")
        return out

    cookies_arg = f'--cookies "{COOKIES_FILE}"' if os.path.exists(COOKIES_FILE) else ''
    env = os.environ.copy()
    env['PATH'] = FFMPEG_BIN + ';' + env.get('PATH', '')

    r = run_cmd(
        f'yt-dlp -f bestaudio -o "{out}" --no-playlist '
        f'--cookies "{COOKIES_FILE}" '
        f'"https://www.bilibili.com/video/{bvid}"',
        env=env, timeout=180
    )

    if r.returncode == 0 and os.path.exists(out):
        log(f" [OK] 音频 {os.path.getsize(out)/1024/1024:.1f}MB")
        return out
    log(f" [FAIL] {r.stderr[-200:]}")
    return None

# ======================= Step 3: 转录 =======================
_wmodel = None
_funasr_model = None

def get_whisper_model():
    global _wmodel
    if _wmodel is not None:
        return _wmodel
    from faster_whisper import WhisperModel
    
    if os.path.exists(WHISPER_MODEL_MEDIUM):
        log(f" [LOAD] 加载 Whisper medium...")
        _wmodel = WhisperModel(WHISPER_MODEL_MEDIUM, device='cpu', compute_type='int8')
    else:
        log(f" [LOAD] 加载 Whisper small...")
        _wmodel = WhisperModel(WHISPER_MODEL_SMALL, device='cpu', compute_type='int8')
    return _wmodel

def get_funasr_model():
    global _funasr_model
    if _funasr_model is not None:
        return _funasr_model
    
    log(f" [LOAD] 加载 SenseVoice-Small...")
    # 将 ffmpeg 路径加入 PATH，确保 FunASR 能调用
    import os as _os
    _os.environ['PATH'] = FFMPEG_BIN + ';' + _os.environ.get('PATH', '')
    sys.path.insert(0, os.path.join(FUNASR_VENV, 'Lib', 'site-packages'))
    from funasr import AutoModel
    _funasr_model = AutoModel(
        model="iic/SenseVoiceSmall",
        device="cpu",
        disable_update=True,
    )
    log(f" [OK] SenseVoice 已加载")
    return _funasr_model

def transcribe(audio_path: str, bvid: str) -> str:
    """转录：优先 Whisper，失败则 FunASR 备用"""
    
    # 检查缓存
    txt_file = os.path.join(TEMP_DIR, f"transcript_{bvid}.txt")
    if os.path.exists(txt_file):
        log(f" [CACHE] 转录已存在")
        return read_file(txt_file)
    
    # 直接指定 FunASR
    if ASR_ENGINE == 'funasr':
        return transcribe_funasr(audio_path, bvid)
    
    # 优先 Whisper
    try:
        model = get_whisper_model()
        log(f" [TRANSCRIBE] Whisper 转录中...")
        segments, _ = model.transcribe(audio_path, language='zh', beam_size=5)
        text = ''.join(s.text.strip() for s in segments).strip()
        if text:
            write_file(txt_file, text)
            log(f" [OK] {len(text)}字")
            return text
    except Exception as e:
        log(f" [WARN] Whisper 失败: {e}")
    
    # 后备 FunASR
    log(f" [INFO] 尝试 FunASR 后备...")
    return transcribe_funasr(audio_path, bvid)

def transcribe_funasr(audio_path: str, bvid: str) -> str:
    """FunASR 转录"""
    txt_file = os.path.join(TEMP_DIR, f"transcript_{bvid}_funasr.txt")
    if os.path.exists(txt_file):
        return read_file(txt_file)
    
    try:
        model = get_funasr_model()
        log(f" [TRANSCRIBE] FunASR 转录中...")
        result = model.generate(input=audio_path, batch_size_s=300, hotword="")
        text = result[0]['text'].strip() if result else ""
        if text:
            text = text.replace('[', '').replace(']', '')
            write_file(txt_file, text)
            log(f" [OK] FunASR: {len(text)}字")
            return text
    except Exception as e:
        log(f" [WARN] FunASR 失败: {e}")
    
    return ""

# ======================= Step 4: md_beautifier =======================
def beautify_file(file_path: str):
    """使用 md_beautifier 美化笔记"""
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from md_beautifier import beautify
        content = read_file(file_path)
        beautified = beautify(content)
        write_file(file_path, beautified)
        log(f" [BEAUTIFY] {os.path.basename(file_path)} 已美化")
    except Exception as e:
        log(f" [WARN] 美化失败: {e}")

# ======================= Step 5: 处理单个UP =======================
def process_up(up: dict, target_date: str):
    name = up['name']
    uid = up['uid']
    log(f"\n{'='*50}")
    log(f"处理 {name} (UID:{uid})")
    log(f"{'='*50}")

    videos = fetch_videos(uid, target_date)
    if not videos:
        log(f" [FAIL] 获取视频列表失败")
        return None

    # 优先匹配当天日期
    today_video = None
    for v in videos:
        if v.get('title_date') == target_date:
            today_video = v
            log(f" [MATCH] {v['title'][:50]}")
            break

    if not today_video:
        today_video = videos[0]
        log(f" [WARN] 未找到{target_date}视频，使用最新: {today_video['title'][:50]}")

    bvid = today_video['bvid']

    # 获取详细信息
    detail = fetch_video_detail(bvid)
    today_video.update(detail)

    # 下载音频
    audio_path = download_audio(bvid)
    if not audio_path:
        return None

    # 转录
    transcript = transcribe(audio_path, bvid)
    today_video['content'] = transcript
    dur = today_video.get('duration', 0)
    today_video['duration_str'] = f"{dur//60}分{dur%60}秒" if dur else "未知"
    log(f" [OK] {len(transcript)}字 | {today_video['duration_str']}")

    return today_video

# ======================= Step 6: 生成笔记 =======================
def generate_notes(up_results: list, target_date: str):
    """生成笔记并美化"""
    from note_formatter import format_note, format_merged_note as fmt_merged

    # 生成各UP单笔记
    for r in up_results:
        if not r:
            continue
        vi = {
            'title': r.get('title', ''),
            'author': r.get('author', ''),
            'uid': r.get('uid', ''),
            'duration': r.get('duration', 0),
            'desc': r.get('desc', ''),
            'url': r.get('url', ''),
            'bvid': r.get('bvid', ''),
        }
        transcript = r.get('content', '')
        up_name = r.get('author', '')
        note_md = format_note(vi, transcript, target_date, up_name, r.get('uid', ''))
        
        safe_name = up_name.replace('/', '_')
        out_file = os.path.join(OUTPUT_DIR, f"{target_date} AI早报-{safe_name}.md")
        write_file(out_file, note_md)
        beautify_file(out_file)  # 美化
        log(f" [OK] {up_name}: {out_file}")

    # 生成综合日报
    merged_md = fmt_merged(up_results, target_date)
    merged_file = os.path.join(OUTPUT_DIR, f"{target_date} AI早报-综合.md")
    write_file(merged_file, merged_md)
    beautify_file(merged_file)  # 美化
    log(f"\n [OK] 综合日报: {merged_file}")

# ======================= 主流程 =======================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)

    target_date = date.today().strftime('%Y-%m-%d')

    log("=" * 55)
    log(" Video News Workflow v3 — 多源综合日报 + 美化")
    log(f" 目标日期: {target_date} | UP主: {len(UP_LIST)}个")
    log(f" ASR引擎: {ASR_ENGINE.upper()}")
    log("=" * 55)

    # 处理各UP
    up_results = []
    for up in UP_LIST:
        result = process_up(up, target_date)
        up_results.append(result)

    valid = [r for r in up_results if r]
    if not valid:
        log("\n[FAIL] 所有UP均处理失败")
        exit(1)

    log(f"\n{'='*55}")
    log(" 生成笔记 + 美化...")
    log(f"{'='*55}")

    generate_notes(valid, target_date)

    log()
    log("=" * 55)
    log(f" 完成! 处理{len(valid)}/{len(UP_LIST)}个UP主")
    log("=" * 55)

if __name__ == '__main__':
    main()