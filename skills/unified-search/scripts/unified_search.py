"""
Unified Search Entry Point v1.0
统一搜索入口 — 根据模式自动路由到最合适的搜索工具

使用方式:
    python unified_search.py "你的问题"                    # 默认通用搜索
    python unified_search.py --mode deep "复杂问题"         # 深度搜索
    python unified_search.py --mode answer "事实问题"       # 快速事实
    python unified_search.py --lang zh "中文问题"           # 中文搜索
    python unified_search.py --github "repo:name"           # GitHub搜索
    python unified_search.py --ai-tools "MCP服务器"         # AI工具搜索
"""

import argparse
import subprocess
import sys
import os

# 技能根目录
SKILLS_ROOT = r"F:\openclaw1\.openclaw\workspace\skills"

# 各工具脚本路径
SCRIPTS = {
    "search_layer": os.path.join(SKILLS_ROOT, "search-layer", "scripts", "search.py"),
    "omni_search": os.path.join(SKILLS_ROOT, "omni-search", "scripts", "omni_search.py"),
    "github_search": "gh",  # CLI
    "github_explorer": os.path.join(SKILLS_ROOT, "github-explorer", "scripts", "explore.py"),
    "multi_search": os.path.join(SKILLS_ROOT, "multi-search-engine", "scripts", "multi_search.py"),
    "multi_simple": os.path.join(SKILLS_ROOT, "multi-search-engine-simple", "scripts", "simple_search.py"),
    "agnxi_search": os.path.join(SKILLS_ROOT, "agnxi-search-skill", "scripts", "agnxi_search.py"),
    "bailian_search": os.path.join(SKILLS_ROOT, "bailian-web-search", "scripts", "bailian_search.py"),
}


def run_search(script_path: str, args: list) -> int:
    """运行搜索脚本"""
    cmd = [sys.executable, script_path] + args
    print(f"[unified-search] Running: {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def run_gh(args: list) -> int:
    """运行 gh CLI"""
    cmd = ["gh"] + args
    print(f"[unified-search] Running: {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def detect_intent(query: str) -> str:
    """根据查询内容自动检测意图"""
    query_lower = query.lower()
    
    if any(kw in query_lower for kw in ["github", "repo", "repository", "gh "]):
        return "github"
    if any(kw in query_lower for kw in ["ai工具", "agent", "mcp", "skill", "工具"]):
        return "ai_tools"
    if any(kw in query_lower for kw in ["代码", "code", "function", "class ", "def "]):
        return "code"
    if any(kw in query_lower for kw in ["中文", "百度", "国内", "微信公众号"]):
        return "zh"
    
    return "general"


def main():
    parser = argparse.ArgumentParser(
        description="Unified Search — 统一搜索入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python unified_search.py "人工智能最新进展"           # 通用搜索
  python unified_search.py --mode deep "量子计算研究"     # 深度搜索
  python unified_search.py --mode answer "地球直径"       # 快速事实
  python unified_search.py --lang zh "国产大模型"        # 中文搜索
  python unified_search.py --github "openai/gpt-4"      # GitHub分析
  python unified_search.py --ai-tools "浏览器自动化"    # AI工具搜索

模式说明:
  general (默认)  - search-layer 主通道，意图感知多源
  deep           - omni-search 全渠道深度并行
  answer         - Tavily AI Answer 快速事实
  news           - 新闻模式，时间排序
  github         - GitHub 代码/仓库搜索
  ai-tools       - AI工具/MCP目录搜索
        """
    )
    
    parser.add_argument("query", nargs="?", help="搜索查询")
    parser.add_argument("--mode", "-m", default="general",
                        choices=["general", "deep", "answer", "news", "github", "ai-tools"],
                        help="搜索模式")
    parser.add_argument("--lang", "-l", default=None,
                        choices=["zh", "en", "all"],
                        help="语言偏好")
    parser.add_argument("--limit", type=int, default=10, help="结果数量")
    parser.add_argument("--freshness", "-f", default=None,
                        help="时间过滤 (pd=一天/pw=一周/pm=一月/py=一年)")
    
    args = parser.parse_args()
    
    # 无参数时显示帮助
    if not args.query and args.mode == "general":
        parser.print_help()
        print("\n[提示] 详情见: skills/unified-search/references/decision-tree.md")
        return 0
    
    # 自动意图检测（当为 general 模式时）
    intent = args.mode
    if intent == "general":
        detected = detect_intent(args.query)
        if detected != "general":
            print(f"[unified-search] 自动检测到意图: {detected}，切换模式")
            intent = detected
    
    # 构建搜索参数
    search_args = [args.query] if args.query else []
    
    if args.freshness:
        search_args.extend(["--freshness", args.freshness])
    
    # 路由到对应工具
    exit_code = 0
    
    if intent == "github":
        # GitHub 专项
        if "/" in (args.query or ""):
            # 视为项目分析
            print(f"[unified-search] GitHub 项目分析模式")
            exit_code = run_search(SCRIPTS["github_explorer"], [args.query])
        else:
            # 仓库搜索
            print(f"[unified-search] GitHub 仓库搜索模式")
            exit_code = run_gh(["search", "repos", args.query, "--limit", str(args.limit)])
    
    elif intent == "ai-tools":
        # AI 工具搜索
        print(f"[unified-search] AI工具/MCP目录搜索")
        exit_code = run_search(SCRIPTS["agnxi_search"], search_args)
    
    elif intent == "zh":
        # 中文搜索
        print(f"[unified-search] 中文搜索模式 → omni-search")
        exit_code = run_search(SCRIPTS["omni_search"], search_args)
    
    elif intent == "deep":
        # 深度搜索
        print(f"[unified-search] 深度搜索模式 → omni-search --depth deep")
        exit_code = run_search(SCRIPTS["omni_search"], ["--depth", "deep"] + search_args)
    
    elif intent == "answer":
        # 快速事实
        print(f"[unified-search] 快速事实模式 → search-layer --mode answer")
        exit_code = run_search(SCRIPTS["search_layer"], ["--mode", "answer"] + search_args)
    
    elif intent == "news":
        # 新闻搜索
        print(f"[unified-search] 新闻搜索模式")
        exit_code = run_search(SCRIPTS["search_layer"], ["--freshness", "pw"] + search_args)
    
    else:
        # 默认通用搜索 → search-layer
        print(f"[unified-search] 通用搜索模式 → search-layer")
        exit_code = run_search(SCRIPTS["search_layer"], search_args)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
