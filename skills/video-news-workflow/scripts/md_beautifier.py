# -*- coding: utf-8 -*-
"""
md_beautifier.py — Markdown Chinese Typography Beautifier v4
"""

import re


def add_chinese_spacing(text):
    """在中文和英文/数字之间加空格"""
    protected = []
    def _p(m):
        protected.append(m.group(0))
        return '\x00P{}P\x00'.format(len(protected)-1)
    text = re.sub(r'https?://\S+', _p, text)
    text = re.sub(r'`[^`]+`', _p, text)
    text = re.sub(r'\[\[[^\]]+\]\]', _p, text)
    text = re.sub(r'#[a-zA-Z0-9_\u4e00-\u9fff-]+', _p, text)
    text = re.sub(r'([a-zA-Z0-9])([\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])', r'\1 \2', text)
    text = re.sub(r'([\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])([a-zA-Z0-9])', r'\1 \2', text)
    for i, ph in enumerate(protected):
        text = text.replace('\x00P{}P\x00'.format(i), ph)
    return text


def fix_punctuation(text):
    """修复标点"""
    text = re.sub(r'([\u4e00-\u9fff\uff00-\uffef]，、；：) +', r'\1', text)
    return text


def format_yaml_block(text):
    """格式化YAML部分"""
    lines = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)$', line)
        if m:
            lines.append('{}: {}'.format(m.group(1), add_chinese_spacing(m.group(2))))
        else:
            lines.append(add_chinese_spacing(line))
    return '\n'.join(lines)


def beautify(text):
    """
    Markdown 完整美化流水线
    1. 空行压缩（最多连续1个）
    2. YAML格式化
    3. 中文间距
    4. 标点修正
    """
    lines = text.split('\n')
    result = []
    blank = 0
    in_code = False
    in_yaml = False

    for line in lines:
        stripped = line.strip()

        # 代码块跟踪
        if stripped.startswith('```'):
            in_code = not in_code
            result.append(line)
            blank = 0
            continue
        if in_code:
            result.append(line)
            continue

        # 空行
        if not stripped:
            blank += 1
            if blank <= 1:
                result.append('')
            continue
        blank = 0

        # YAML frontmatter
        if stripped == '---':
            result.append(line)
            in_yaml = not in_yaml
            continue
        if in_yaml:
            result.append(format_yaml_block(line))
            continue

        # 标题
        if stripped.startswith('#'):
            line = add_chinese_spacing(line)
            result.append(line)
            continue

        # 表格行（保持原样）
        if stripped.startswith('|'):
            result.append(line)
            continue

        # 列表项
        if re.match(r'^(\s*)[-*+]\s', stripped) or re.match(r'^(\s*)\d+\.\s', stripped):
            line = re.sub(r'^(\s*)\d+\.\s+', r'\1- ', line)
            line = add_chinese_spacing(line)
            result.append(line)
            continue

        # 普通文本
        line = add_chinese_spacing(line)
        line = fix_punctuation(line)
        result.append(line)

    # 清理首尾空行
    while result and not result[0].strip():
        result.pop(0)
    while result and not result[-1].strip():
        result.pop()

    return '\n'.join(result)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
        content = open(path, encoding='utf-8').read()
        result = beautify(content)
        open(path, 'w', encoding='utf-8').write(result)
        print('Beautified: ' + path)
    else:
        print('Usage: python md_beautifier.py <file.md>')
