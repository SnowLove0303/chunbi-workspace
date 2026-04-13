"""
lobster workflow step 入口
把 Python 脚本变成 lobster 可调用的 step

用法 - lobster Workflow YAML:
  - id: my-step
    run: python lobster_steps.py --action run_workflow --workflow "${workflow_file}"

lobster 变量通过环境变量或 JSON 文件传入
"""
import argparse
import json
import sys
import os
from pathlib import Path

# 路径
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SKILL_DIR))

from browser_control.client import run_actions, BrowserClient, DEFAULT_CDP_URL

OUTPUT_DIR = SKILL_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ──────────────────────────────────────────
# lobster step 实现
# ──────────────────────────────────────────

def step_run_workflow(workflow_file: str,
                      cdp_url: str = DEFAULT_CDP_URL,
                      output_name: str = "workflow_result.json") -> int:
    """
    执行 workflow JSON/YAML 文件
    lobster 调用:
      python lobster_steps.py --action run_workflow --workflow ${workflow_file}
    """
    wf_path = Path(workflow_file).resolve()
    if not wf_path.exists():
        wf_path = SKILL_DIR / workflow_file
    if not wf_path.exists():
        print(f"[X] Workflow 文件不存在: {workflow_file}")
        return 1

    # 支持 JSON / YAML
    with open(wf_path, "r", encoding="utf-8") as f:
        if wf_path.suffix in (".yaml", ".yml"):
            import yaml
            data = yaml.safe_load(f)
        else:
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

    # 打印摘要
    ok_steps = sum(1 for s in result["steps"] if s.get("ok"))
    failed_steps = [s for s in result["steps"] if not s.get("ok")]

    print(f"\n[RESULT] 成功: {ok_steps}/{len(result['steps'])} 步")
    if result.get("extracted"):
        print(f"  提取字段: {list(result['extracted'].keys())}")
    if result.get("screenshots"):
        print(f"  截图: {len(result['screenshots'])} 张")
    if failed_steps:
        print(f"\n[FAILURES]")
        for s in failed_steps:
            err = s.get("error", "?")
            act = s.get("action", "?")
            print(f"  - {act}: {err[:80]}")

    return 1 if failed_steps else 0


def step_navigate(url: str, wait_until: str = "load",
                  cdp_url: str = DEFAULT_CDP_URL) -> int:
    """单步导航"""
    print(f"[=] 导航: {url}")
    result = run_actions(
        [{"action": "nav", "url": url, "wait_until": wait_until}],
        cdp_url=cdp_url
    )
    print(f"[+] URL: {result['final_url']}")
    print(f"    标题: {result['title']}")
    return 0 if result["steps"][0].get("ok") else 1


def step_screenshot(path: str, full_page: bool = True,
                    cdp_url: str = DEFAULT_CDP_URL) -> int:
    """单步截图"""
    if not Path(path).is_absolute():
        path = str(OUTPUT_DIR / "screenshots" / Path(path).name)
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    print(f"[=] 截图: {path}")
    result = run_actions(
        [{"action": "screenshot", "path": path, "full_page": full_page}],
        cdp_url=cdp_url
    )
    ok = result["screenshots"] and len(result["screenshots"]) > 0
    print(f"[{'+' if ok else 'X'}] {'截图成功' if ok else '截图失败'}")
    return 0 if ok else 1


def step_click(selector: str, timeout: int = 30000,
               cdp_url: str = DEFAULT_CDP_URL) -> int:
    """单步点击"""
    print(f"[=] 点击: {selector}")
    result = run_actions(
        [{"action": "click", "selector": selector, "timeout": timeout}],
        cdp_url=cdp_url
    )
    ok = result["steps"][0].get("ok")
    print(f"[{'+' if ok else 'X'}] 点击{'成功' if ok else '失败'}")
    return 0 if ok else 1


def step_type(selector: str, text: str, clear: bool = True,
              cdp_url: str = DEFAULT_CDP_URL) -> int:
    """单步输入"""
    preview = text[:40] + "..." if len(text) > 40 else text
    print(f"[=] 输入 → {selector}: {preview}")
    result = run_actions(
        [{"action": "type", "selector": selector, "text": text, "clear": clear}],
        cdp_url=cdp_url
    )
    ok = result["steps"][0].get("ok")
    print(f"[{'+' if ok else 'X'}] 输入{'成功' if ok else '失败'}")
    return 0 if ok else 1


def step_fill(selector: str, text: str, timeout: int = 30000,
             cdp_url: str = DEFAULT_CDP_URL) -> int:
    """单步 fill（React/Vue 受控组件）"""
    preview = text[:40] + "..." if len(text) > 40 else text
    print(f"[=] Fill → {selector}: {preview}")
    result = run_actions(
        [{"action": "fill", "selector": selector, "text": text, "timeout": timeout}],
        cdp_url=cdp_url
    )
    ok = result["steps"][0].get("ok")
    print(f"[{'+' if ok else 'X'}] Fill{'成功' if ok else '失败'}")
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
            print(f"  {k}: {str(v)[:80]}")
        output_path = OUTPUT_DIR / "extracted.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(extracted, f, ensure_ascii=False, indent=2)
        print(f"[+] 已保存: {output_path}")
    ok = result["steps"][0].get("ok")
    return 0 if ok else 1


def step_interactive(cdp_url: str = DEFAULT_CDP_URL) -> int:
    """
    交互模式 - 每行一个 JSON 动作，输入空行执行
    用于人工调试:
      python lobster_steps.py --action interactive
    """
    print("[=] 交互模式（每行 JSON 动作，空行结束）：")
    actions = []
    while True:
        try:
            line = input(">>> ")
        except EOFError:
            break
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

    print(f"\n[结果]  URL: {result['final_url']}")
    print(f"        标题: {result['title']}")
    print(f"        步数: {len(result['steps'])}")
    for i, s in enumerate(result["steps"], 1):
        icon = "[+]" if s.get("ok") else "[X]"
        act = s.get("action", "?")
        err = f" | {s.get('error', '')[:60]}" if not s.get("ok") else ""
        print(f"  {i}. {icon} {act}{err}")

    if result.get("extracted"):
        print(f"\n[提取]")
        for k, v in result["extracted"].items():
            print(f"  {k}: {str(v)[:80]}")

    return 0


# ──────────────────────────────────────────
# CLI 入口
# ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="browser-control lobster steps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
动作:
  run_workflow  执行 workflow JSON/YAML 文件
  navigate      导航到 URL
  screenshot    截图
  click         点击元素
  type          输入文本（清空再输入）
  fill          输入文本（直接设置值，React）
  extract       提取元素内容
  interactive   交互模式（调试用）

示例:
  python lobster_steps.py --action navigate --url "https://baidu.com"
  python lobster_steps.py --action click --selector "#kw"
  python lobster_steps.py --action run_workflow --workflow "examples/baidu_search.json"
  python lobster_steps.py --action interactive
        """
    )
    parser.add_argument("--action", "-a", required=True,
                        choices=["run_workflow", "navigate", "screenshot",
                                 "click", "type", "fill", "extract", "interactive"],
                        help="执行的动作")
    # run_workflow
    parser.add_argument("--workflow", help="workflow 文件路径")
    parser.add_argument("--workflow-output", default="workflow_result.json")
    # navigate
    parser.add_argument("--url", help="目标 URL")
    parser.add_argument("--wait-until", default="load")
    # screenshot
    parser.add_argument("--path", "-p", help="截图路径")
    parser.add_argument("--full-page", action="store_true", default=True)
    # click / type / fill / extract
    parser.add_argument("--selector", "-s", help="CSS selector")
    parser.add_argument("--timeout", type=int, default=30000)
    # type / fill
    parser.add_argument("--text", "-t", help="输入文本")
    parser.add_argument("--clear", type=lambda x: x.lower() == "true",
                        default=True)
    # extract
    parser.add_argument("--attr", help="提取属性（空=文本）")
    parser.add_argument("--as-key", help="提取结果键名")
    # common
    parser.add_argument("--cdp-url", default=DEFAULT_CDP_URL)

    args = parser.parse_args()

    # Windows UTF-8
    if sys.stdout.encoding != "utf-8":
        sys.stdout = open(sys.stdout.fileno(), mode="w",
                         encoding="utf-8", errors="replace")

    try:
        if args.action == "run_workflow":
            if not args.workflow:
                print("[X] --workflow required")
                return 1
            return step_run_workflow(args.workflow,
                                   cdp_url=args.cdp_url,
                                   output_name=args.workflow_output)

        elif args.action == "navigate":
            if not args.url:
                print("[X] --url required")
                return 1
            return step_navigate(args.url,
                               wait_until=args.wait_until,
                               cdp_url=args.cdp_url)

        elif args.action == "screenshot":
            if not args.path:
                print("[X] --path required")
                return 1
            return step_screenshot(args.path,
                                 full_page=args.full_page,
                                 cdp_url=args.cdp_url)

        elif args.action == "click":
            if not args.selector:
                print("[X] --selector required")
                return 1
            return step_click(args.selector,
                            timeout=args.timeout,
                            cdp_url=args.cdp_url)

        elif args.action == "type":
            if not args.selector or not args.text:
                print("[X] --selector and --text required")
                return 1
            return step_type(args.selector, args.text,
                           clear=args.clear, cdp_url=args.cdp_url)

        elif args.action == "fill":
            if not args.selector or not args.text:
                print("[X] --selector and --text required")
                return 1
            return step_fill(args.selector, args.text,
                           timeout=args.timeout, cdp_url=args.cdp_url)

        elif args.action == "extract":
            if not args.selector:
                print("[X] --selector required")
                return 1
            return step_extract(args.selector,
                               attr=args.attr,
                               as_key=args.as_key,
                               cdp_url=args.cdp_url)

        elif args.action == "interactive":
            return step_interactive(cdp_url=args.cdp_url)

    except KeyboardInterrupt:
        print("\n[ABORT] 用户中断")
        return 130
    except Exception as e:
        print(f"[X] 异常: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
