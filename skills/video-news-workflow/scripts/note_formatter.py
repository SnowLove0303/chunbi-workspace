# -*- coding: utf-8 -*-
"""
note_formatter.py - Bilibili 视频笔记格式化器 v6
- SenseVoice 特殊标签过滤
- 更强片头片尾去除
- 语义段落切分(不是逐关键词切)
"""

import re
from datetime import datetime


def to_simplified(text: str) -> str:
    if not text:
        return text
    try:
        import opencc
        converter = opencc.OpenCC('t2s')
        return converter.convert(text)
    except ImportError:
        return text


def is_opening(text: str) -> bool:
    if not text or len(text) < 5:
        return True
    if len(text) > 150:
        return False
    _OPENS = ['各位觀眾','各位观众','早上好','今天是','週日','周日','歡迎收看','欢迎收看']
    text_stripped = text.strip()
    return any(
        text_stripped == op or text_stripped.startswith(op + ' ') or text_stripped.startswith(op + ',')
        for op in _OPENS if len(op) <= len(text_stripped)
    )


# ============ 清洗 ============
def _clean_text(text: str) -> str:
    """清洗 ASR 乱码、特殊标签"""
    # 1. 去除 SenseVoice 特殊标签
    text = re.sub(r'<\|\w+\|>', '', text)          # <|zh|> <|HAPPY|> <|Speech|> <|woitn|> 等
    text = re.sub(r'<[^>]{1,20}>', '', text)      # 其他尖括号标签

    # 2. 去除 <em> 标签
    text = re.sub(r'<em class="keyword">', '', text)
    text = text.replace('</em>', '')

    # 3. 去除零宽字符
    text = text.replace('\u200b', '')

    # 4. 去除控制字符
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)

    # 5. 修复被 ASR 分词的字母拼写 (如 "g p t" → "GPT")
    # 5a. 精准替换有空格分隔的字母词（ASR 输出有时全拼有时分词）
    _subs_spaced = [
        # (原始带空格文本, 替换结果)
        ('g p t', 'GPT'), ('a g i', 'AGI'), ('o p e n a i', 'OpenAI'),
        ('s p o t', 'Sora'), ('e g p u', 'eGPU'), ('i p c', 'IPC'),
        ('p c', 'PC'), ('g p', 'GP'), ('a i', 'AI'),
        ('y o u r d a y', 'YourDay'), ('t e n c e n t a i', 'TencentAI'),
        ('t e n d a i', 'TencentAI'), ('t e n c e n t', 'Tencent'),
        ('c l a u d e', 'Claude'), ('o p u s', 'Opus'),
        ('g r e g m a n', 'Gregman'), ('open cloud', 'OpenCloud'),
    ]
    for spaced, result in _subs_spaced:
        # 把 "a b c" → "a\\s+b\\s+c"，然后 re.sub
        pattern = re.sub(r' ', r'\\s+', spaced)  # 'g p t' → 'g\s+p\s+t'
        # 替换结果去掉空格：'GPT' (直接用result，result本身没有空格)
        text = re.sub(pattern, result, text, flags=re.IGNORECASE)

    # 5b. 通用合并：只合并 ASCII 字母（不管中文字符）
    def merge_spaced_letters(text):
        result = []
        i = 0
        while i < len(text):
            # 只处理 ASCII 字母（不管中文字符）
            if text[i].isalpha() and ord(text[i]) < 128 and i + 2 < len(text):
                letters = []
                j = i
                while j < len(text) and (text[j] == ' ' or (text[j].isalpha() and ord(text[j]) < 128)):
                    if text[j] != ' ':
                        letters.append(text[j].lower())
                    j += 1
                if len(letters) >= 3:
                    result.append(''.join(letters))
                    i = j
                    continue
            result.append(text[i])
            i += 1
        return ''.join(result)
    text = merge_spaced_letters(text)

    # 5c. 处理已合并的小写缩写词 + 特殊词组
    for pat, repl in [
        # 核心缩写（字母词）
        (r'spot', 'Sora'),
        (r'gpt', 'GPT'),
        (r'openai', 'OpenAI'),
        (r'agi', 'AGI'),
        (r'openclaw', 'OpenClaw'),
        (r'claude', 'Claude'),
        (r'gp(?!p)', 'GP'),
        (r'api', 'API'),
        (r'ipc', 'IPC'),
        (r'pc', 'PC'),
        (r'egpu', 'eGPU'),
        (r'opus(?!p)', 'Opus'),
        (r'yourday', 'YourDay'),
        (r'pro(?!p)', 'Pro'),
        (r'gregman', 'Gregman'),
        (r'ai(?![a-zA-Z])', 'AI'),
        # TencentAI 系列
        (r'tendaimemory', 'TencentAI Memory'),
        (r'tencentai', 'TencentAI'),
        (r'tencent(?!ai)', 'Tencent'),
        # OpenClaw Memory
        (r'opencloudmemory', 'OpenClaw Memory'),
        (r'openclaw\s*memory', 'OpenClaw Memory'),
    ]:
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)

    # 6. 清理多余空格
    text = re.sub(r'[ \u00a0]{2,}', ' ', text)  # 多个空格变一个
    text = text.strip()

    return text


# ============ 主题检测 ============
TOPIC_PATTERNS = [
    (r'GPT-?[五六4-6]|GPT\s*[五六4-6]', 'GPT/AI模型'),
    (r'OpenAI|ChatGPT|人工智能|AGI|Sora', 'AI模型'),
    (r'Anthropic|Claude|Opus', 'Anthropic'),
    (r'苹果|Apple|Mac\b|iPhone|iPad|eGPU', 'Apple'),
    (r'谷歌|Google|Gemini|Android', 'Google'),
    (r'微软|Microsoft|Copilot|Windows', 'Microsoft'),
    (r'腾讯|微信|openclaw|OpenClaw|tencent', '腾讯'),
    (r'小米|小爱|Xiaomi|笔记本|IPC', '小米'),
    (r'医保|医院|医疗|诊断|国家医保局', '医疗健康'),
    (r'特斯拉|Tesla|FSD|自动驾驶', '特斯拉'),
    (r'Meta|Facebook|Llama|雷朋', 'Meta'),
    (r'字节|抖音|TikTok|豆包', '字节'),
    (r'阿里|通义|Qwen|阿里巴巴', '阿里'),
    (r'英伟达|NVIDIA|GPU|黄仁勋', '英伟达'),
    (r'开源|发布|更新|上线|推出', '产品发布'),
    (r'漏洞|安全|攻击|隐私|数据泄露', '安全事件'),
    (r'融资|收购|上市|估值|IPO', '商业财经'),
]


def _find_major_topics(text: str) -> list:
    """
    找出文本中的主要主题段落,每个主题至少覆盖150字。
    返回 [(topic_label, start, end), ...]
    """
    # 收集所有匹配
    matches = []
    for pat, label in TOPIC_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            matches.append((m.start(), m.end(), label))

    if not matches:
        return []

    # 按位置排序,去重
    matches = sorted(set(matches), key=lambda x: x[0])

    # 合并相邻/重叠的匹配,形成主题段落
    blocks = []
    current_label = None
    current_start = None
    current_end = None

    for start, end, label in matches:
        if current_label is None:
            current_label = label
            current_start = start
            current_end = end
        elif label == current_label and start - current_end < 80:
            # 同主题且距离近,扩展
            current_end = max(current_end, end)
        elif start - current_end > 200:
            # 与前一个主题距离超过200字,结束当前段,开启新段
            blocks.append((current_label, current_start, current_end))
            current_label = label
            current_start = start
            current_end = end
        else:
            # 切换主题
            blocks.append((current_label, current_start, current_end))
            current_label = label
            current_start = start
            current_end = end

    if current_label is not None:
        blocks.append((current_label, current_start, current_end))

    return blocks


def _split_into_paragraphs(text: str) -> list:
    """将文本切分为语义段落,每段包含足够内容"""
    if len(text) < 50:
        return [{'title': None, 'content': text}]

    blocks = _find_major_topics(text)

    if not blocks:
        # 无主题,按长度均匀分段
        return _split_by_length(text)

    paragraphs = []

    # 第一段:从开头到第一个主题
    first_start = blocks[0][1]
    if first_start > 10:
        intro = text[:first_start].strip()
        if intro and len(intro) > 5 and not is_opening(intro):
            paragraphs.append({'title': None, 'content': intro})

    # 主体段落
    for i, (label, start, end) in enumerate(blocks):
        # 扩展段落:向前包含前导内容,向后包含后续内容(直到下个主题或足够长度)
        seg_start = start
        seg_end = min(end + 300, len(text))  # 主题词往后取300字
        if i + 1 < len(blocks):
            seg_end = min(seg_end, blocks[i+1][1])

        content = text[seg_start:seg_end].strip()
        if content and len(content) > 5 and not is_opening(content):
            paragraphs.append({'title': label, 'content': content})

    # 过滤太短的段落(少于30字)
    result = [p for p in paragraphs if len(p['content']) >= 30]

    return result if result else paragraphs[:1] if paragraphs else [{'title': None, 'content': text}]


def _split_by_length(text: str) -> list:
    """按标点/长度均匀分段"""
    target = 200
    if len(text) <= target:
        return [{'title': None, 'content': text}]

    # 按句子切分
    sentences = re.split(r'([。!?;])', text)
    chunks = []
    for i in range(0, len(sentences) - 1, 2):
        combined = (sentences[i] + sentences[i+1]).strip()
        if combined:
            chunks.append(combined)
    if len(sentences) % 2 == 1 and sentences[-1].strip():
        chunks.append(sentences[-1].strip())

    if not chunks:
        return [{'title': None, 'content': text}]

    # 合并成段落
    result = []
    current = []
    current_len = 0
    for chunk in chunks:
        current.append(chunk)
        current_len += len(chunk)
        if current_len >= target or len(current) >= 5:
            content = ''.join(current).strip()
            if content:
                result.append({'title': None, 'content': content})
            current = []
            current_len = 0
    if current:
        content = ''.join(current).strip()
        if content:
            result.append({'title': None, 'content': content})

    return result if result else [{'title': None, 'content': text}]


# ============ 结构化解析 ============
_TIME_PAT = re.compile(r'^(\d{2}:\d{2})[\s\xa0]*(.{3,})$')
_NUM_PAT  = re.compile(r'^(\d)\.\s+(.{3,60})$')


def _parse_structured(text: str) -> tuple:
    """解析有时间戳或编号的结构化文本"""
    # 预处理：统一 \xa0 为普通空格（修复 _clean_text 删除 \xa0 导致的匹配失败）
    text = text.replace('\xa0', ' ')
    # 注意：不合并 \s+，保留换行符以支持多行结构化文本

    sections = []
    body_parts = []
    lines = text.split('\n')
    i = 0
    current = None

    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line or is_opening(line):
            continue

        m_time = _TIME_PAT.match(line)
        m_num = _NUM_PAT.match(line)

        if m_time:
            if current:
                sections.append(current)
            current = {'time': m_time.group(1), 'title': m_time.group(2)[:60], 'body': ''}
        elif m_num:
            if current:
                sections.append(current)
            body_lines = []
            while i < len(lines):
                nxt = lines[i].strip()
                i += 1
                if not nxt:
                    continue
                if _NUM_PAT.match(nxt):
                    i -= 1
                    break
                body_lines.append(nxt)
            title = m_num.group(2)
            full = (title + '\n' + '\n'.join(body_lines)).strip()
            current = {'time': '', 'title': title[:60], 'body': full}
        else:
            body_parts.append(line)

    if current:
        sections.append(current)

    return sections, body_parts


# ============ 格式化 ============
def _format_paragraphs_raw(text: str) -> str:
    """将段落列表格式化为 markdown"""
    paragraphs = _split_into_paragraphs(text)

    parts = []
    for p in paragraphs:
        title = p.get('title')
        content = p['content'].strip()
        if not content:
            continue

        # 清理内容中的残余标签
        content = re.sub(r'<\|\w+\|>', '', content)
        content = re.sub(r'[ \u00a0]{2,}', ' ', content)
        content = content.strip()

        if title:
            parts.append(f"**{title}**\n\n{content}")
        else:
            parts.append(content)

    return '\n\n'.join(parts) if parts else text


def format_note(video_info: dict, transcript: str, date: str, up_name: str, up_uid: str) -> str:
    """格式化笔记"""
    title    = video_info.get('title', '无标题')
    duration = video_info.get('duration', 0)
    url      = video_info.get('url', f"https://www.bilibili.com/video/{video_info.get('bvid','')}")
    bvid     = video_info.get('bvid', '')
    desc     = video_info.get('desc', '')

    dur_str = f"{duration//60}分{duration%60}秒" if duration else "未知"
    wd = ['周一','周二','周三','周四','周五','周六','周日']
    wday = wd[datetime.strptime(date, '%Y-%m-%d').weekday()]

    # 选择内容源
    desc_has_structure = bool(re.search(r'\d{2}:\d{2}', desc))
    raw = desc if (desc and (desc_has_structure or len(desc) >= len(transcript))) else transcript

    # 清洗 + 繁简转换
    raw = _clean_text(raw)
    raw = to_simplified(raw)

    # 同时清洗 transcript（备用内容源）
    transcript_clean = _clean_text(transcript)
    transcript_clean = to_simplified(transcript_clean)
    # 去除片头片尾：直接用固定标记删除，不依赖中文关键词
    # 片头：删到 "Anthropic" 关键词之前（即：开头 → Anthropic 第一次出现）
    anthropic_idx = transcript_clean.lower().find('anthropic')
    if anthropic_idx > 5:
        transcript_clean = transcript_clean[anthropic_idx:].strip()
    # 片尾：删掉 "资讯播送完了" 及之后的内容
    for ending in ['资讯播送完了', '明天的资讯播送完了', '今天的资讯播送完了', '明天见', '感谢观看', 'the end']:
        idx = transcript_clean.rfind(ending)
        if idx > 5:
            transcript_clean = transcript_clean[:idx].strip()
    # 去除片尾不完整句
    transcript_clean = re.sub(r'标志着今天的[\s\S]*$', '', transcript_clean).strip()

    # 片头片尾去除（对 raw）
    # 直接用 ASCII 关键词定位，不用中文 lookahead
    for kw in ['Anthropic', '苹果批准', '谷歌', '小米', '腾讯']:
        idx = raw.lower().find(kw.lower())
        if 5 < idx < 200:
            raw = raw[idx:].strip()
            break
    # 片尾
    for ending in ['资讯播送完了', '明天的资讯播送完了', '今天的资讯播送完了', '明天见', '感谢观看']:
        idx = raw.rfind(ending)
        if idx > 5:
            raw = raw[:idx].strip()

    # 2. 去除结尾(找到最后一个常见结尾词)
    for ending in ['资讯播送完了', '明天的资讯播送完了', '今天的资讯播送完了', '明天见', '感谢观看']:
        idx = raw.rfind(ending)  # 用 rfind 找最后一个
        if idx > 0:
            raw = raw[:idx].strip()

    # 3. 去除末尾不完整句(如"标志着今天的")
    raw = re.sub(r'标志着今天的[\s\S]*$', '', raw).strip()
    raw = re.sub(r'标志着.*$', '', raw).strip()

    # 检测结构化内容
    has_timestamp = bool(re.search(r'\d{2}:\d{2}', raw))
    has_numbering = bool(re.search(r'^\d+\.', raw, re.MULTILINE))

    if has_timestamp or has_numbering:
        secs, body_parts = _parse_structured(raw)

        # 如果 section body 全为空，尝试从 transcript 补充内容
        if secs and all(not s.get('body', '').strip() for s in secs) and transcript_clean:
            _TOPIC_KEYWORDS = {
                'Anthropic': ['anthropic', 'claude', 'opus'],
                'Apple': ['apple', 'mac', 'gpu', 'silicon', 'egpu'],
                'Google': ['google', 'gemini', 'android'],
                'OpenAI': ['openai', 'gpt', 'chatgpt', 'sora', 'agi'],
                'Linux': ['linux', '漏洞', '安全'],
                'Tencent': ['openclaw', 'opencloud', 'tencentai', 'tencent'],
            }
            prev_end = 0
            for sec in secs:
                title_lower = sec.get('title', '').lower()
                # 找到该 section 对应的关键词
                matched_kw = None
                matched_label = None
                for label, kws in _TOPIC_KEYWORDS.items():
                    if label.lower() in title_lower or any(kw in title_lower for kw in kws):
                        matched_kw = kws
                        matched_label = label
                        break
                if matched_kw:
                    # 从上一次搜索结束位置之后找关键词（避免重叠）
                    search_from = prev_end
                    found_idx = -1
                    for kw in matched_kw:
                        idx = transcript_clean.lower().find(kw, search_from)
                        if idx >= 0:
                            found_idx = idx
                            break
                    if found_idx < 0:
                        # 如果在后面找不到，往前扩大搜索范围但不超过 transcript 开头
                        for kw in matched_kw:
                            idx = transcript_clean.lower().find(kw)
                            if idx >= 0:
                                found_idx = idx
                                break
                    if found_idx >= 0:
                        # 从关键词位置向前扩展 20 字符（包含上下文）
                        start = max(0, found_idx - 20)
                        # 每个 section 平均分配剩余内容（约 300 字符 / 4 ≈ 75 字符）
                        seg_len = max(60, (len(transcript_clean) - found_idx) // max(1, len(secs)))
                        end = min(len(transcript_clean), found_idx + seg_len)
                        body_candidate = transcript_clean[start:end].strip()
                        if len(body_candidate) > 15:
                            sec['body'] = body_candidate
                            prev_end = end

        pts = []
        for s in secs[:6]:
            if s.get('time'):
                pts.append(f"{s['time']} {s['title']}")
            else:
                pts.append(s['title'])
        points_md = '\n'.join(f"{i}. {p}" for i, p in enumerate(pts, 1))

        sec_md = []
        for i, s in enumerate(secs, 1):
            t = s.get('title', '')
            b = s.get('body', '')
            if b and b.startswith(t):
                b = b[len(t):].strip()
            if b:
                sec_md.append(f"### {i}. {t}\n\n{b}")
            else:
                sec_md.append(f"### {i}. {t}")
        sec_md.extend(body_parts)
        secs_str = '\n\n'.join(sec_md) if sec_md else _format_paragraphs_raw(raw if transcript_clean != _clean_text(transcript) else transcript_clean)
    else:
        pts = []
        points_md = ''
        secs_str = _format_paragraphs_raw(raw if transcript_clean != _clean_text(transcript) else transcript_clean)

    fm = f"""---
date: {date}
source: Bilibili
up: {up_name}
video: {title}
url: {url}
tags:
  - AI早报
  - 实时快报
---"""

    note = f"""{fm}

# {title}

> 日期: {date}({wday})
> UP主: {up_name}
> 原始视频: [{title}]({url})

---

## 视频信息

| 属性 | 值 |
|------|-----|
| 时长 | {dur_str} |
| BV ID | {bvid} |
| UP主 | {up_name} |
| 标签 | AI早报、{date} |

---

## 今日要点

{points_md if points_md else '(见详细内容)'}

---

## 详细内容

{secs_str}

---

## 相关链接

- [原视频]({url})
- [UP主主页](https://space.bilibili.com/{up_uid})

---

*由「春笔 ✒️」自动生成 | {date}*
"""
    return note


def format_merged_note(up_results: list, date: str) -> str:
    """生成综合日报"""
    wd = ['周一','周二','周三','周四','周五','周六','周日']
    wday = wd[datetime.strptime(date, '%Y-%m-%d').weekday()]

    blocks = []
    for r in up_results:
        if not r:
            continue
        vi = {
            'title':    r.get('title', ''),
            'author':   r.get('author', ''),
            'uid':      r.get('uid', ''),
            'duration': r.get('duration', 0),
            'desc':     r.get('desc', ''),
            'url':      r.get('url', ''),
            'bvid':     r.get('bvid', ''),
        }
        tr  = r.get('content', '') or r.get('transcript', '')
        un  = r.get('author', '')
        uid = vi['uid']
        note = format_note(vi, tr, date, un, uid)
        # 去掉 frontmatter
        lines = note.split('\n')
        start = 0
        dash_count = 0
        for j, ln in enumerate(lines):
            if ln.strip() == '---':
                dash_count += 1
                if dash_count == 1: start = j + 1
                elif dash_count == 2: start = j + 1; break
        blocks.append('\n'.join(lines[start:]))

    combined = '\n\n---\n\n'.join(blocks)

    merged = f"""# AI 早报 {date}(综合版)

**日期:** {date}({wday})
**来源:** {' + '.join(r.get('author','') for r in up_results if r)}
**生成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

{combined}

---

> 💡 本日报由「春笔 ✒️」自动整理 | 数据来源: Bilibili 视频
"""
    return merged
