"""
lobster workflow step 入口 - 把 Python 脚本变成 lobster 可调用的 step
用法: 在 YAML workflow 里写:
  - id: my-step
    run: python lobster_steps.py --action run_workflow --workflow "${workflow_file}"

lobster 变量通过环境变量或 JSON 文件传入
"""
import argparse, json, sys, os
from pathlib import Path

# 把 browser_control 包加入路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from browser_control.client import run_actions, BrowserClient, DEFAULT_CDP_URL

SKILL_DIR = Path(__file__).parent.parent
OUTPUT_DIR = SKILL_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ──────────────────────────────────────────
# lobster step 实现
# ──────────────────────────────────────────

def step_run_workflow(workflow_file: str, cdp_url: str = DEFAULT_CDP_URL,
                      output_name: str = "workflow_result.json") -> int:
    """
    执行 workflow JSON 文件
    lobster 调用: python lobster_steps.py --action run_workflow --workflow ${workflow_file}
    """
    wf_path = Path(workflow_file).resolve()
    if not wf_path.exists():
        # 可能是相对路径，尝试相对于 SKILL_DIR
        wf_path = SKILL_DIR / workflow_file
    if not wf_path.exists():
        print(f"[X] Workflow 文件不存在: {workflow_file}")
        return 1

    with open(wf_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    steps = data if isinstance(data, list) else data.get("steps", [])
    if not steps:
        print("[X] Workflow 为空或格式错误")
        return 1

    print(f"[=] 执行 workflow: {wf_path.name}, {len(steps)} 步")

    result = run_actions(steps, cdp_url=cdp_url)

    # 保存结果
    output_path = OUTPUT_DIR / output_name
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[+] 结果已保存: {output_path}")

    # 打印摘要
    ok_steps = sum(1 for s in result["steps"] if s.get("ok"))
    print(f"    成功: {ok_steps}/{len(result['steps'])} 步")
    if result.get("extracted"):
        print(f"    提取字段: {list(result['extracted'].keys())}")
    if result.get("screenshots"):
        print(f"    截图: {len(result['screenshots'])} 张")

    # 有失败 step 返回非零
    failed = [s for s in result["steps"] if not s.get("ok")]
    return 1 if failed else 0


def step_navigate(url: str, wait_until: str = "load", cdp_url: str = DEFAULT_CDP_URL) -> int:
    """单步导航"""
    print(f"[=] 导航到: {url}")
    result = run_actions([{"action": "nav", "url": url, "wait_until": wait_until}], cdp_url=cdp_url)
    print(f"[+] 当前URL: {result['final_url']}")
    print(f"    标题: {result['title']}")
    return 0 if result["steps"][0].get("ok") else 1


def step_screenshot(path: str, full_page: bool = True,
                    cdp_url: str = DEFAULT_CDP_URL) -> int:
    """单步截图"""
    print(f"[=] 截图: {path}")
    # 确保路径是绝对路径
    if not Path(path).is_absolute():
        path = str(OUTPUT_DIR / "screenshots" / Path(path).name)
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    result = run_actions([{"action": "screenshot", "path": path, "full_page": full_page}],
                         cdp_url=cdp_url)
    print(f"[+] 截图完成: {result['screenshots']}")
    return 0 if result["screenshots"] else 1


def step_click(selector: str, timeout: int = 30000, cdp_url: str = DEFAULT_CDP_URL) -> int:
    """单步点击"""
    print(f"[=] 点击: {selector}")
    result = run_actions([{"action": "click", "selector": selector, "timeout": timeout}],
                         cdp_url=cdp_url)
    ok = result["steps"][0].get("ok")
    print(f"[{'+' if ok else 'X'}] 点击{'成功' if ok else '失败'}")
    return 0 if ok else 1


def step_type(selector: str, text: str, clear: bool = True,
              cdp_url: str = DEFAULT_CDP_URL) -> int:
    """单步输入"""
    print(f"[=] 输入文本到 {selector}: {text[:50]}{'...' if len(text) > 50 else ''}")
    result = run_actions([{"action": "type", "selector": selector, "text": text, "clear": clear}],
                         cdp_url=cdp_url)
    ok = result["steps"][0].get("ok")
    print(f"[{'+' if ok else 'X'}] 输入{'成功' if ok else '失败'}")
    return 0 if ok else 1


def step_extract(selector: str, attr: str = None, text: bool = True,
                as_key: str = None, cdp_url: str = DEFAULT_CDP_URL) -> int:
    """单步提取"""
    print(f"[=] 提取: {selector}")
    args = {"selector": selector, "text": text}
    if attr:
        args["attr"] = attr
    if as_key:
        args["as"] = as_key

    result = run_actions([{"action": "extract", **args}], cdp_url=cdp_url)
    extracted = result.get("extracted", {})
    if extracted:
        for k, v in extracted.items():
            print(f"    {k}: {str(v)[:100]}")
        # 保存提取结果
        output_path = OUTPUT_DIR / "extracted.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(extracted, f, ensure_ascii=False, indent=2)
        print(f"[+] 提取结果已保存: {output_path}")
    ok = result["steps"][0].get("ok")
    return 0 if ok else 1


def step_interactive(cdp_url: str = DEFAULT_CDP_URL) -> int:
    """
    交互模式 - 通过 stdin 接收动作序列
    用于人工调试阶段:
      python lobster_steps.py --action interactive
      然后输入: {"action":"nav","url":"https://..."}
      每行一个 JSON 动作
    """
    print("[=] 交互模式（输入 JSON 动作，每行一个，输入空行结束）:")
    actions = []
    while True:
        line = input()
        if not line.strip():
            break
        try:
            actions.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"[!] JSON 解析失败: {e}")

    if not actions:
        print("[X] 无动作")
        return 0

    print(f"[=] 执行 {len(actions)} 个动作...")
    result = run_actions(actions, cdp_url=cdp_url)

    print(f"\n[结果] URL: {result['final_url']}")
    print(f"       标题: {result['title']}")
    print(f"       步数: {len(result['steps'])}")
    for i, s in enumerate(result["steps"]):
        status = "[+]" if s.get("ok") else "[X]"
        action = s.get("action", "?")
        extra = ", ".join(f"{k}={v}" for k, v in s.items() if k not in ("ok", "action"))
        print(f"  {i+1}. {status} {action} {extra}")

    if result.get("extracted"):
        print(f"\n[提取数据]")
        for k, v in result["extracted"].items():
            print(f"  {k}: {str(v)[:80]}")

    return 0


# ──────────────────────────────────────────
# CLI 入口
# ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="browser-control lobster steps")
    parser.add_argument("--action", "-a", required=True,
                        choices=["run_workflow", "navigate", "screenshot",
                                 "click", "type", "extract", "interactive"],
                        help="执行的动作")
    # run_workflow
    parser.add_argument("--workflow", help="workflow JSON 文件路径")
    parser.add_argument("--workflow-output", default="workflow_result.json",
                        help="结果输出文件名")
    # navigate
    parser.add_argument("--url", help="目标 URL")
    parser.add_argument("--wait-until", default="load",
                        help="wait_until: load/domcontentloaded/networkidle")
    # screenshot
    parser.add_argument("--path", "-p", help="截图/输出路径")
    parser.add_argument("--full-page", action="store_true", default=True,
                        help="全页截图")
    # click
    parser.add_argument("--selector", "-s", help="CSS selector")
    parser.add_argument("--timeout", type=int, default=30000)
    # type
    parser.add_argument("--text", "-t", help="输入文本")
    parser.add_argument("--clear", type=bool, default=True)
    # extract
    parser.add_argument("--attr", help="提取属性（None=文本）")
    parser.add_argument("--as-key", help="提取结果保存的键名")
    # common
    parser.add_argument("--cdp-url", default=DEFAULT_CDP_URL,
                        help=f"Chrome CDP URL (默认: {DEFAULT_CDP_URL})")

    args = parser.parse_args()

    # Windows UTF-8 输出
    if sys.stdout.encoding != "utf-8":
        sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")

    try:
        if args.action == "run_workflow":
            if not args.workflow:
                print("[X] --workflow required")
                return 1
            return step_run_workflow(args.workflow, cdp_url=args.cdp_url,
                                     output_name=args.workflow_output)

        elif args.action == "navigate":
            if not args.url:
                print("[X] --url required")
                return 1
            return step_navigate(args.url, wait_until=args.wait_until, cdp_url=args.cdp_url)

        elif args.action == "screenshot":
            if not args.path:
                print("[X] --path required")
                return 1
            return step_screenshot(args.path, full_page=args.full_page, cdp_url=args.cdp_url)

        elif args.action == "click":
            if not args.selector:
                print("[X] --selector required")
                return 1
            return step_click(args.selector, timeout=args.timeout, cdp_url=args.cdp_url)

        elif args.action == "type":
            if not args.selector or not args.text:
                print("[X] --selector and --text required")
                return 1
            return step_type(args.selector, args.text, clear=args.clear, cdp_url=args.cdp_url)

        elif args.action == "extract":
            if not args.selector:
                print("[X] --selector required")
                return 1
            return step_extract(args.selector, attr=args.attr, as_key=args.as_key,
                               cdp_url=args.cdp_url)

        elif args.action == "interactive":
            return step_interactive(cdp_url=args.cdp_url)

    except Exception as e:
        print(f"[X] 异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main() or 0)
