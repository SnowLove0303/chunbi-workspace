"""
lobster workflow YAML 模板替换执行器
原理：在 lobster 之前，用 Python 把变量替换进 YAML，
      生成临时 workflow 文件，再交给 lobster 执行。
"""
import subprocess, json, os, sys, tempfile, hashlib
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
LOBSTER_BIN = Path.home() / "AppData/Roaming/npm/node_modules/@clawdbot/lobster/bin/lobster.js"
TEMPLATE_YAML = SCRIPT_DIR / "browser-precision-workflow.yaml"


def render_template(template_path, variables):
    """把变量替换进 YAML 模板"""
    content = template_path.read_text(encoding="utf-8")

    # 简单的 ${var} -> value 替换
    for key, val in variables.items():
        placeholder = "${" + key + "}"
        # 对于路径类变量，转为正斜杠路径
        if isinstance(val, str) and ("/" in val or "\\" in val):
            val = val.replace("\\", "/")
        content = content.replace(placeholder, str(val))

    return content


def run_lobster_workflow(variables, dry_run=False, timeout=120):
    """
    执行 lobster workflow
    variables: dict，键值对会被替换进 YAML 模板
    """
    if not LOBSTER_BIN.exists():
        return {"ok": False, "error": f"lobster not found: {LOBSTER_BIN}"}

    # 生成临时文件
    rendered = render_template(TEMPLATE_YAML, variables)
    temp_fd, temp_path = tempfile.mkstemp(suffix=".yaml", prefix="lobster_workflow_")
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            f.write(rendered)

        # 构建命令
        args_json = json.dumps(variables, ensure_ascii=False)
        cmd = [
            "node", str(LOBSTER_BIN),
            "run",
            "--file", temp_path,
            "--args-json", args_json,
            "--mode", "tool"
        ]

        if dry_run:
            cmd.insert(2, "--dry-run")

        print(f"[LOBSTER] Executing workflow with variables: {list(variables.keys())}")

        result = subprocess.run(
            cmd,
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=timeout,
            cwd=str(SCRIPT_DIR)
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if stdout:
            try:
                parsed = json.loads(stdout)
                return parsed
            except json.JSONDecodeError:
                return {"ok": result.returncode == 0, "raw": stdout, "stderr": stderr}

        if result.returncode != 0:
            return {"ok": False, "stderr": stderr, "rc": result.returncode}

        return {"ok": True}

    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="lobster workflow executor")
    parser.add_argument("--target", "-t", default="https://www.baidu.com")
    parser.add_argument("--output", "-o", default="./output/result.json")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    screenshot_path = str(SKILL_DIR / "screenshots" / "lobster_result.png")
    output_path = str((SKILL_DIR / args.output.lstrip("./")).resolve())

    variables = {
        "target_url": args.target,
        "screenshot_path": screenshot_path,
        "output_file": output_path,
        "chrome_port": "9222",
        "gateway_port": "18789",
    }

    print("=" * 50)
    print(f"[LOBSTER WORKFLOW] target={args.target}")
    print("=" * 50)

    result = run_lobster_workflow(variables, dry_run=args.dry_run)

    if args.dry_run:
        print("[DRY RUN] Workflow prepared (temp YAML deleted after parse)")
        sys.exit(0)

    print(f"\n[LOBSTER] ok={result.get('ok')} status={result.get('status', '-')}")

    if not result.get("ok"):
        err = result.get("error", {})
        if isinstance(err, dict):
            print(f"[X] lobster error: {err.get('message', err)}")
        else:
            print(f"[X] lobster error: {err}")
        sys.exit(1)
    else:
        print(f"[+] lobster workflow completed successfully")
        sys.exit(0)
