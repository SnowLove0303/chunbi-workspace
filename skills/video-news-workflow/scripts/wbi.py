# -*- coding: utf-8 -*-
"""
Bilibili WBI 签名模块
从 yt_dlp bilibili.py 提取并简化
用法:
    from wbi import get_wbi_signed_url
    url = get_wbi_signed_url(base_url, params, bvid)
"""

import hashlib
import time
import urllib.parse
import requests

_WBI_KEY_CACHE = {}

_MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52,
]

_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.bilibili.com/',
}


def _get_wbi_key(bvid: str) -> str:
    """获取 WBI 混合密钥，带 30 秒缓存"""
    global _WBI_KEY_CACHE
    if time.time() < _WBI_KEY_CACHE.get('ts', 0) + 25:
        return _WBI_KEY_CACHE['key']

    url = 'https://api.bilibili.com/x/web-interface/nav'
    r = requests.get(url, headers=_HEADERS, timeout=10,
                     proxies={'http': None, 'https': None})
    data = r.json()

    wbi_img = data.get('data', {}).get('wbi_img', {})
    img_url = wbi_img.get('img_url', '')
    sub_url = wbi_img.get('sub_url', '')

    # 从 URL 中提取文件名（不含扩展名）作为 key 字符
    img_key = img_url.rpartition('/')[2].partition('.')[0]
    sub_key = sub_url.rpartition('/')[2].partition('.')[0]
    key = img_key + sub_key

    # 混合加密
    mixed = ''.join(key[i] for i in _MIXIN_KEY_ENC_TAB)[:32]

    _WBI_KEY_CACHE = {'key': mixed, 'ts': time.time()}
    return mixed


def _sign_wbi(params: dict, bvid: str) -> dict:
    """
    对参数进行 WBI 签名
    返回添加了 wts 和 w_rid 的新参数
    """
    # 过滤特殊字符
    params = {
        k: ''.join(c for c in str(v) if c not in "!'()*")
        for k, v in params.items()
    }
    params['wts'] = str(round(time.time()))

    # 按 key 排序
    sorted_items = sorted(params.items())
    query = urllib.parse.urlencode(sorted_items)

    wbi_key = _get_wbi_key(bvid)
    params['w_rid'] = hashlib.md5(f'{query}{wbi_key}'.encode()).hexdigest()

    return params


def get_signed_url(base_url: str, params: dict, bvid: str) -> str:
    """
    拼接带 WBI 签名的完整 URL
    示例:
        url = get_signed_url(
            'https://api.bilibili.com/x/web-interface/wbi/search/all/v2',
            {'keyword': 'OpenClaw', 'page': 1},
            'BV123456'
        )
    """
    signed = _sign_wbi(params.copy(), bvid)
    return f"{base_url}?{urllib.parse.urlencode(signed)}"


def search_with_wbi(keyword: str, page: int = 1, page_size: int = 20) -> dict:
    """
    使用 WBI 签名进行全站搜索
    返回原始 JSON 数据（调用方自行解析）
    """
    bvid = 'test'  # 搜索不需要真实 bvid，用任意值即可
    base_url = 'https://api.bilibili.com/x/web-interface/wbi/search/all/v2'
    params = {
        'keyword': keyword,
        'page': page,
        'page_size': page_size,
        'search_source_type': 1,
    }
    signed = _sign_wbi(params, bvid)
    url = f"{base_url}?{urllib.parse.urlencode(signed)}"

    r = requests.get(url, headers=_HEADERS, timeout=10,
                     proxies={'http': None, 'https': None})
    return r.json()
