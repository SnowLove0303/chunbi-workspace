@echo off
REM md_beautifier 测试脚本
cd /d "%~dp0"

echo === 测试 beautifier ===
python -c "import sys; sys.path.insert(0, '.'); from md_beautifier import beautify; print(beautify('# Test\n\n中文English混合text\n\n- 列表项1\n- 列表项2\n\n| 列1 | 列2 |\n|------|------|\n| A   | B   |'))"

echo.
echo === 检查语法 ===
python -m py_compile md_beautifier.py && echo 语法OK || echo 语法错误

echo.
echo === 美化示例笔记 ===
python md_beautifier.py ..\..\..\..\Users\chenz\Documents\Obsidian Vault\实时快报\2026-04-05\AI早报-综合.md
