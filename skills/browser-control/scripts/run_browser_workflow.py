"""一键运行浏览器工作流 - 精准控制闭环方案配套

支持两种执行引擎：
  --engine playwright  (默认) 直接调用 playwright CLI
  --engine lobster     通过 lobster workflow YAML 执行

 lobster 执行路径：
  lobster run browser-precision-workflow.yaml
    --args-json '{"target_url":"...", "screenshot_path":"..."}'
    --mode tool

前置条件：
  1. Chrome 调试端口 9222 已启动
  2. lobster CLI 已安装 (npm i -g @clawdbot/lobster)
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
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
CHECK_PORT_SCRIPT = SCRIPT_DIR / "check_ports.py"
WORKFLOW_YAML = SCRIPT_DIR / "browser-precision-workflow.yaml"
LOBSTER_BIN = Path.home() / "AppData/Roaming/npm/node_modules/@clawdbot/lobster/bin/lobster.js"


def run_cmd(cmd, timeout=30, cwd=None):
    """执行命令，返回 (returncode, stdout, stderr)"""
    preview = cmd[:80] + '...' if len(cmd) > 80 else cmd
    print(f"[CMD] {preview}")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            encoding='utf-8', errors='replace',
            timeout=timeout, cwd=cwd or SCRIPT_DIR
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"


def check_ports():
    """端口预检"""
    print("\n" + "=" * 50)
    print("[STEP1] 端口预检")
    print("=" * 50)
    code, out, err = run_cmd(f'python "{CHECK_PORT_SCRIPT}"', timeout=15)
    print(out)
    if err:
        print(f"[!] stderr: {err[:200]}")
    return code == 0


def ensure_chrome():
    """确保 Chrome 调试模式运行"""
    print("\n" + "=" * 50)
    print("[STEP2] 确保 Chrome 调试模式")
    print("=" * 50)

    code, _, _ = run_cmd(
        'curl -s --connect-timeout 3 http://127.0.0.1:9222/json/version',
        timeout=8
    )
    if code == 0:
        print("[+] Chrome 调试端口已就绪")
        return True

    print("[!] Chrome 未检测到，尝试启动...")
    if platform.system() == "Windows":
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_path):
            chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        if os.path.exists(chrome_path):
            subprocess.Popen(
                f'"{chrome_path}" --remote-debugging-port=9222 '
                f'--user-data-dir="{os.getenv("TEMP")}\\chrome_debug" '
                f'--no-first-run --no-default-browser-check',
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        else:
            print("[X] 未找到 Chrome，请手动启动:")
            print('   chrome.exe --remote-debugging-port=9222')
            return False
    else:
        subprocess.Popen(
            'google-chrome --remote-debugging-port=9222 '
            '--user-data-dir=/tmp/chrome_debug --no-sandbox',
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    print("[WAIT] 等待 Chrome 启动（5s）...")
    time.sleep(5)
    code, _, _ = run_cmd(
        'curl -s --connect-timeout 5 http://127.0.0.1:9222/json/version',
        timeout=8
    )
    if code == 0:
        print("[+] Chrome 调试端口已就绪")
        return True
    print("[X] Chrome 启动失败")
    return False


def prepare_dirs():
    """准备输出目录"""
    print("\n" + "=" * 50)
    print("[STEP3] 准备工作目录")
    print("=" * 50)
    for d in ["checkpoints", "screenshots", "output"]:
        target = SKILL_DIR / d
        target.mkdir(exist_ok=True)
        print(f"  [+] {target}")
    return True


# ─────────────────────────────────────────────
# 引擎A：Playwright CLI（直接，已验证）
# ─────────────────────────────────────────────
def run_playwright(target_url, output_file):
    """Playwright CLI 全页截图"""
    print("\n" + "=" * 50)
    print(f"[ENGINE-A] Playwright CLI 截图")
    print("=" * 50)

    screenshot_path = SKILL_DIR / "screenshots" / "page.png"

    cmd = (
        f'npx playwright screenshot '
        f'--channel chrome '
        f'--full-page '
        f'"{target_url}" '
        f'"{screenshot_path}"'
    )
    code, out, err = run_cmd(cmd, timeout=60)

    print(out)
    if err:
        print(f"[!] stderr: {err[:300]}")

    if code == 0 and screenshot_path.exists():
        print(f"[+] 截图已保存: {screenshot_path}")
        result = {"url": target_url, "screenshot": str(screenshot_path), "status": "success"}
        output_path = SKILL_DIR / output_file.lstrip("./")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[+] 结果已保存: {output_path}")
        return True
    print("[X] 截图失败")
    return False


# ─────────────────────────────────────────────
# 引擎B：lobster Workflow（体系化作战）
# ─────────────────────────────────────────────
def run_lobster(target_url, screenshot_path, output_file):
    """lobster workflow YAML 执行"""
    print("\n" + "=" * 50)
    print(f"[ENGINE-B] lobster Workflow 执行")
    print("=" * 50)

    lobster_js = LOBSTER_BIN
    if not lobster_js.exists():
        print(f"[X] lobster CLI 未找到: {lobster_js}")
        print("    安装: npm i -g @clawdbot/lobster")
        return False

    # lobster workflow args
    args = {
        "target_url": target_url,
        "screenshot_path": str(Path(screenshot_path).as_posix()),
        "chrome_port": "9222",
        "gateway_port": "18789",
        "output_file": str(Path(output_file).as_posix()),
    }
    args_json = json.dumps(args, ensure_ascii=False)

    # 工作目录切换到 scripts/（lobster 在这里找 relative path）
    cmd = [
        "node", str(lobster_js),
        "run",
        "--file", str(WORKFLOW_YAML.resolve()),
        "--args-json", args_json,
        "--mode", "tool"
    ]
    cmd_str = " ".join(f'"{a}"' if " " in str(a) else a for a in cmd)
    print(f"[CMD] {cmd_str[:120]}...")

    try:
        result = subprocess.run(
            cmd, shell=False,
            capture_output=True, text=True,
            encoding='utf-8', errors='replace',
            timeout=120,
            cwd=str(SCRIPT_DIR)
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if stdout:
            try:
                parsed = json.loads(stdout)
                print(f"[LOBSTER] ok={parsed.get('ok')} status={parsed.get('status','-')}")
                if not parsed.get('ok') and parsed.get('error'):
                    print(f"[X] lobster error: {parsed['error'].get('message','?')}")
                    if stderr:
                        print(f"    stderr: {stderr[:300]}")
                    return False
                return True
            except json.JSONDecodeError:
                print(f"[LOBSTER] raw output: {stdout[:500]}")
                if stderr:
                    print(f"    stderr: {stderr[:300]}")

        if result.returncode != 0 and not stdout:
            print(f"[X] lobster 执行失败 (rc={result.returncode})")
            if stderr:
                print(f"    stderr: {stderr[:300]}")
            return False

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("[X] lobster 执行超时（120s）")
        return False
    except Exception as e:
        print(f"[X] lobster 异常: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="浏览器精准控制工作流运行器")
    parser.add_argument("--target", "-t", default="https://www.example.com",
                        help="目标 URL")
    parser.add_argument("--output", "-o", default="./output/result.json",
                        help="输出文件路径")
    parser.add_argument("--engine", "-e", default="playwright",
                        choices=["playwright", "lobster", "auto"],
                        help="执行引擎: playwright(默认)|lobster|auto(优先lobster)")
    parser.add_argument("--dry-run", action="store_true",
                        help="lobster dry-run 模式")

    args = parser.parse_args()

    print("=" * 50)
    print(f"[RUN] 浏览器精准控制工作流 (引擎: {args.engine})")
    print("=" * 50)
    print(f"  目标: {args.target}")
    print(f"  输出: {args.output}")

    # 1. 端口预检
    if not check_ports():
        resp = input("[!] 端口检测失败，是否继续？ (y/N): ")
        if resp.lower() != 'y':
            sys.exit(1)

    # 2. Chrome
    if not ensure_chrome():
        resp = input("[!] Chrome 启动失败，是否继续？ (y/N): ")
        if resp.lower() != 'y':
            sys.exit(1)

    # 3. 目录
    prepare_dirs()

    # 4. 执行
    screenshot_path = SKILL_DIR / "screenshots" / "lobster_page.png"

    if args.engine in ("lobster", "auto"):
        # lobster dry-run
        if args.dry_run:
            lobster_js = LOBSTER_BIN
            if lobster_js.exists():
                cmd = ["node", str(lobster_js), "run", "--dry-run",
                       "--file", str(WORKFLOW_YAML.resolve())]
                subprocess.run(cmd, cwd=str(SCRIPT_DIR))
            else:
                print("[X] lobster 未安装，跳过 dry-run")
            sys.exit(0)

        success = run_lobster(args.target, screenshot_path, args.output)
        if not success and args.engine == "auto":
            print("[!] lobster 失败，切换到 Playwright CLI")
            success = run_playwright(args.target, args.output)
    else:
        success = run_playwright(args.target, args.output)

    print("\n" + "=" * 50)
    if success:
        print("[+] 工作流执行成功")
    else:
        print("[X] 工作流执行失败")
    print("=" * 50)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
