"""
browser-control 工作流一键运行器

用法:
  python run_browser_workflow.py --target "https://www.example.com"
  python run_browser_workflow.py --workflow "examples/baidu_search.json"
  python run_browser_workflow.py --target "..." --engine lobster --dry-run
"""
import subprocess
import sys
import os
import time
import io
import json
import platform
import argparse
from pathlib import Path

# Windows GBK 兼容
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
CHECK_PORT_SCRIPT = SCRIPT_DIR / "check_ports.py"
WORKFLOW_YAML = SCRIPT_DIR / "browser-precision-workflow.yaml"
LOBSTER_BIN = Path.home() / "AppData/Roaming/npm/node_modules/@clawdbot/lobster/bin/lobster.js"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CHROME_PATH_ALT = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"


# ──────────────────────────────────────────
# 端口检测
# ──────────────────────────────────────────

def check_port(host: str = "127.0.0.1", port: int = 9222,
              timeout: int = 3) -> bool:
    """检测端口是否开放"""
    import socket
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def probe_cdp(port: int = 9222) -> dict:
    """探测 CDP 版本信息"""
    import urllib.request
    try:
        url = f"http://127.0.0.1:{port}/json/version"
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read())
    except Exception:
        return {}


# ──────────────────────────────────────────
# Chrome 管理
# ──────────────────────────────────────────

def ensure_chrome(port: int = 9222, user_data_dir: str = None,
                 timeout: int = 10) -> bool:
    """
    确保 Chrome 调试模式运行

    1. 探测端口是否就绪
    2. 未就绪则启动 Chrome
    3. 等待就绪
    返回: True = 就绪
    """
    print(f"\n[Chrome] 检测调试端口 {port}...")

    if check_port("127.0.0.1", port):
        info = probe_cdp(port)
        if info:
            browser = info.get("browser", "?")
            print(f"[+] Chrome 已就绪: {browser}")
            return True

    print("[!] Chrome 未启动，启动中...")

    # 找 Chrome
    chrome_paths = [CHROME_PATH, CHROME_PATH_ALT]
    chrome_exe = None
    for p in chrome_paths:
        if os.path.exists(p):
            chrome_exe = p
            break

    if not chrome_exe:
        # 尝试 PATH 中找
        for name in ["chrome.exe", "chrome"]:
            try:
                result = subprocess.run(
                    ["where", name], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    chrome_exe = result.stdout.strip().splitlines()[0]
                    break
            except Exception:
                pass

    if not chrome_exe:
        print("[X] 未找到 Chrome，请手动启动：")
        print('    chrome.exe --remote-debugging-port=9222')
        return False

    # 启动参数
    user_data = user_data_dir or os.path.join(os.getenv("TEMP", "."), "chrome_debug_openclaw")
    os.makedirs(user_data, exist_ok=True)

    cmd = (
        f'"{chrome_exe}" '
        f"--remote-debugging-port={port} "
        f'--user-data-dir="{user_data}" '
        f"--no-first-run --no-default-browser-check "
        f"--no-sandbox "
        f"--disable-dev-shm-usage"
    )

    print(f"[Chrome] 启动: {os.path.basename(chrome_exe)} --remote-debugging-port={port}")
    subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=0 if platform.system() != "Windows" else 0x08000000
    )

    # 等待就绪
    print(f"[Chrome] 等待启动（最多 {timeout}s）...")
    for i in range(timeout):
        time.sleep(1)
        if check_port("127.0.0.1", port):
            info = probe_cdp(port)
            browser = info.get("browser", "?")
            print(f"[+] Chrome 已就绪: {browser}（启动耗时 {i+1}s）")
            return True
        if i == timeout - 1:
            break
        print(f"  等待中... ({i+1}/{timeout}s)", end="\r")

    print(f"[X] Chrome 启动超时（{timeout}s）")
    return False


# ──────────────────────────────────────────
# 执行引擎
# ──────────────────────────────────────────

def run_playwright(target_url: str, output_file: str = "./output/result.json",
                  screenshot: str = "./screenshots/page.png") -> bool:
    """
    引擎A: Playwright CLI 截图
    最简单直接的执行方式
    """
    print(f"\n[Engine-A] Playwright CLI | {target_url}")

    screenshot_path = SKILL_DIR / "screenshots" / "page.png"

    cmd = (
        f'npx playwright screenshot '
        f'--channel chrome '
        f'--full-page '
        f'"{target_url}" '
        f'"{screenshot_path}"'
    )

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=60, cwd=str(SKILL_DIR)
        )
    except subprocess.TimeoutExpired:
        print("[X] Playwright 执行超时（60s）")
        return False

    if result.stdout:
        for line in result.stdout.splitlines():
            if line.strip():
                print(f"  {line.strip()}")
    if result.returncode != 0 and result.stderr:
        err_lines = result.stderr.strip().splitlines()
        for line in err_lines[:5]:
            if line.strip():
                print(f"  [!] {line.strip()}")

    if result.returncode == 0 and screenshot_path.exists():
        size_kb = screenshot_path.stat().st_size / 1024
        print(f"[+] 截图成功: {screenshot_path.name} ({size_kb:.1f}KB)")

        result_data = {
            "url": target_url,
            "screenshot": str(screenshot_path),
            "screenshot_size_kb": round(size_kb, 1),
            "engine": "playwright_cli",
            "status": "success"
        }
        out_path = SKILL_DIR / output_file.lstrip("./")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        print(f"[+] 结果已保存: {out_path.name}")
        return True

    print(f"[X] Playwright 执行失败（rc={result.returncode}）")
    return False


def run_lobster(target_url: str, workflow_file: str = None,
               screenshot_path: str = None,
               output_file: str = "workflow_result.json") -> bool:
    """
    引擎B: lobster Workflow YAML 执行
    体系化作战，带 checkpoint + 验证
    """
    lobster_js = LOBSTER_BIN

    if not lobster_js.exists():
        print(f"[X] lobster CLI 未安装，跳转到 Engine-A")
        return False

    print(f"\n[Engine-B] lobster Workflow")

    wf = workflow_file or WORKFLOW_YAML
    ss_path = screenshot_path or "screenshots/page.png"

    args = {
        "target_url": target_url,
        "screenshot_path": str(Path(ss_path).as_posix()),
        "chrome_port": "9222",
        "output_file": str(Path(output_file).as_posix()),
    }
    args_json = json.dumps(args, ensure_ascii=False)

    cmd = [
        "node", str(lobster_js),
        "run",
        "--file", str(wf.resolve()),
        "--args-json", args_json,
        "--mode", "tool"
    ]

    print(f"[lobster] {wf.name}")
    try:
        result = subprocess.run(
            cmd, shell=False,
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=120, cwd=str(SCRIPT_DIR)
        )
    except subprocess.TimeoutExpired:
        print("[X] lobster 执行超时（120s）")
        return False
    except Exception as e:
        print(f"[X] lobster 异常: {e}")
        return False

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    if stdout:
        try:
            parsed = json.loads(stdout)
            ok = parsed.get("ok", False)
            status = parsed.get("status", "-")
            steps = parsed.get("steps", [])
            print(f"[lobster] ok={ok} status={status} steps={len(steps)}")
            if not ok and parsed.get("error"):
                err = parsed["error"]
                print(f"[X] lobster 错误: {err.get('message', err)}")
            if stderr and len(stderr) < 300:
                print(f"  stderr: {stderr}")
            return ok
        except json.JSONDecodeError:
            if stdout:
                print(f"[lobster] {stdout[:200]}")
                if stderr and len(stderr) < 300:
                    print(f"  stderr: {stderr[:200]}")

    if result.returncode != 0:
        print(f"[X] lobster failed (rc={result.returncode})")
        if stderr:
            print(f"  {stderr[:300]}")
        return False

    return result.returncode == 0


# ──────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="browser-control 工作流运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_browser_workflow.py --target "https://baidu.com"
  python run_browser_workflow.py --workflow "examples/baidu_search.json"
  python run_browser_workflow.py --target "..." --engine lobster --dry-run
  python run_browser_workflow.py --list-engines
        """
    )
    parser.add_argument("--target", "-t",
                        default="https://www.example.com",
                        help="目标 URL")
    parser.add_argument("--workflow", "-w",
                        help="workflow 文件路径（默认: browser-precision-workflow.yaml）")
    parser.add_argument("--output", "-o",
                        default="./output/result.json",
                        help="输出文件路径")
    parser.add_argument("--engine", "-e",
                        choices=["playwright", "lobster", "auto"],
                        default="auto",
                        help="引擎: playwright(快速截图) | lobster(体系化) | auto(先lobster失败再playwright)")
    parser.add_argument("--no-chrome", action="store_true",
                        help="跳过 Chrome 启动检查")
    parser.add_argument("--chrome-port", type=int, default=9222,
                        help="Chrome 调试端口")
    parser.add_argument("--dry-run", action="store_true",
                        help="lobster dry-run 模式")
    parser.add_argument("--list-engines", action="store_true",
                        help="列出可用引擎")

    args = parser.parse_args()

    # 列出引擎
    if args.list_engines:
        print("可用引擎:")
        print(f"  playwright  Playwright CLI 截图（快速简单）")
        lobster_status = "✓" if LOBSTER_BIN.exists() else "✗"
        print(f"  lobster      lobster Workflow YAML {lobster_status}")
        print(f"  auto         lobster 失败后自动回退到 playwright")
        print(f"\nlobster 路径: {LOBSTER_BIN}")
        return 0

    # 准备输出目录
    for d in ["checkpoints", "screenshots", "output"]:
        (SKILL_DIR / d).mkdir(exist_ok=True)

    # Chrome
    if not args.no_chrome:
        ready = ensure_chrome(port=args.chrome_port)
        if not ready:
            resp = input("Chrome 未就绪，是否继续？(y/N): ").strip().lower()
            if resp != "y":
                return 1

    print(f"\n{'='*50}")
    print(f"[RUN] target={args.target}")
    print(f"      engine={args.engine}")
    print(f"      output={args.output}")
    print(f"{'='*50}")

    success = False

    # lobster dry-run
    if args.dry_run and args.engine in ("lobster", "auto"):
        lobster_js = LOBSTER_BIN
        if lobster_js.exists():
            wf = args.workflow or WORKFLOW_YAML
            cmd = ["node", str(lobster_js), "run", "--dry-run",
                   "--file", str(wf.resolve())]
            subprocess.run(cmd, cwd=str(SCRIPT_DIR))
        else:
            print("[X] lobster 未安装")
        return 0

    # 执行
    if args.engine in ("lobster", "auto"):
        success = run_lobster(
            target_url=args.target,
            workflow_file=args.workflow,
            output_file=args.output
        )
        if not success and args.engine == "auto":
            print("[!] lobster 失败，自动回退到 Playwright CLI")
            success = run_playwright(args.target, args.output)

    if args.engine == "playwright":
        success = run_playwright(args.target, args.output)

    # 结果
    print(f"\n{'='*50}")
    if success:
        print(f"[✓] 工作流执行成功")
    else:
        print(f"[✗] 工作流执行失败")
    print(f"{'='*50}")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main() or 0)
