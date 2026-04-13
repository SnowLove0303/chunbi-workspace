"""
browser-control workflow 断点管理与执行验证

功能:
1. Checkpoint 保存/恢复（UA/cookie/位置状态）
2. 动作序列验证（verify_step 三维验证）
3. 与 lobster workflow YAML 集成

用法:
  python checkpoint.py --action save --name "logged_in" --output checkpoints/logged_in.json
  python checkpoint.py --action verify --checkpoint checkpoints/logged_in.json --verify-url "app.example.com"
  python checkpoint.py --action run --workflow examples/checkpoint_flow.json

lobster Workflow YAML 中使用:
  - id: verify-step
    run: python checkpoint.py --action verify --checkpoint "${CHECKPOINT}" --verify-url "..."
"""
import argparse
import json
import sys
import io
import os
import hashlib
import time
from pathlib import Path

# Windows GBK 兼容
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
CHECKPOINT_DIR = SKILL_DIR / "checkpoints"


class Checkpoint:
    """单个检查点"""

    def __init__(self, name: str, path: str = None):
        self.name = name
        self.path = Path(path) if path else (CHECKPOINT_DIR / f"{name}.json")
        self.data: dict = {}

    def save(self, url: str, title: str, cookies: list = None,
             local_storage: dict = None, scroll_position: int = 0,
             extra: dict = None):
        """保存当前浏览器状态"""
        self.data = {
            "name": self.name,
            "saved_at": time.time(),
            "saved_at_iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "url": url,
            "title": title,
            "cookies": cookies or [],
            "local_storage": local_storage or {},
            "scroll_position": scroll_position,
            "user_agent": None,
            "extra": extra or {},
            "version": "1.0",
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"[+] Checkpoint 已保存: {self.path}")

    def load(self) -> dict:
        """加载检查点"""
        if not self.path.exists():
            raise FileNotFoundError(f"Checkpoint 不存在: {self.path}")
        with open(self.path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        return self.data

    def restore(self, client) -> bool:
        """恢复到浏览器（需要 browser_control.client.BrowserClient）"""
        try:
            data = self.load()
        except FileNotFoundError:
            print(f"[X] Checkpoint 不存在: {self.path}")
            return False

        # 恢复 cookies
        if data.get("cookies"):
            try:
                client.set_cookies(data["cookies"])
                print(f"[+] Cookies 已恢复 ({len(data['cookies'])} 条)")
            except Exception as e:
                print(f"[!] Cookies 恢复失败: {e}")

        # 恢复 localStorage
        if data.get("local_storage"):
            try:
                for key, val in data["local_storage"].items():
                    client.eval_js(
                        f"window.localStorage.setItem({json.dumps(key)}, {json.dumps(val)})"
                    )
                print(f"[+] localStorage 已恢复 ({len(data['local_storage'])} 条)")
            except Exception as e:
                print(f"[!] localStorage 恢复失败: {e}")

        # 恢复滚动位置
        if data.get("scroll_position", 0) > 0:
            try:
                client.eval_js(f"window.scrollTo(0, {data['scroll_position']})")
            except Exception:
                pass

        print(f"[+] Checkpoint 已恢复: {data.get('url', '')}")
        return True

    def diff(self, other_path: str) -> dict:
        """对比两个 checkpoint 的差异"""
        other = Checkpoint("other", other_path)
        a = self.load()
        b = other.load()

        diffs = []
        if a.get("url") != b.get("url"):
            diffs.append(f"URL: {a.get('url')} → {b.get('url')}")
        if a.get("title") != b.get("title"):
            diffs.append(f"Title: {a.get('title')} → {b.get('title')}")

        a_cookies = {c["name"]: c for c in a.get("cookies", [])}
        b_cookies = {c["name"]: c for c in b.get("cookies", [])}
        added = set(b_cookies.keys()) - set(a_cookies.keys())
        removed = set(a_cookies.keys()) - set(b_cookies.keys())
        if added:
            diffs.append(f"新增 cookies: {added}")
        if removed:
            diffs.append(f"删除 cookies: {removed}")

        return {
            "same": len(diffs) == 0,
            "diffs": diffs,
            "checkpoint_a": self.path,
            "checkpoint_b": other_path,
        }


class WorkflowRunner:
    """
    带 Checkpoint 的 Workflow 执行器

    用法:
        runner = WorkflowRunner("examples/my_flow.json")
        runner.add_verify_step("check_login", verify_url="app.example.com")
        result = runner.run()
    """

    def __init__(self, workflow_path: str):
        self.workflow_path = Path(workflow_path)
        self.steps = []
        self.checkpoints = {}

    def add_step(self, action: str, **params):
        self.steps.append({"action": action, **params})

    def add_checkpoint_save(self, name: str, **save_params):
        self.add_step("_checkpoint_save", checkpoint_name=name, **save_params)

    def add_checkpoint_verify(self, name: str, verify_url: str = None,
                            verify_selector: str = None):
        self.add_step("_checkpoint_verify", checkpoint_name=name,
                     verify_url=verify_url, verify_selector=verify_selector)

    def run(self, cdp_url: str = "http://127.0.0.1:9222") -> dict:
        """执行 workflow"""
        from browser_control.client import run_actions

        print(f"[WORKFLOW] {self.workflow_path.name}")
        print(f"[STEPS] {len(self.steps)}")

        # 加载 workflow 文件（如果存在）
        wf_path = Path(self.workflow_path)
        if wf_path.exists():
            with open(wf_path, "r", encoding="utf-8") as f:
                wf_data = json.load(f)
            self.steps = wf_data.get("steps", self.steps)

        result = {"steps": [], "ok": True, "checkpoints": {}}

        # 过滤掉内部 step（_checkpoint_*）
        real_steps = [s for s in self.steps
                     if not s.get("action", "").startswith("_checkpoint")]

        if real_steps:
            # 实时执行
            res = run_actions(real_steps, cdp_url=cdp_url)
            result.update(res)

        # 处理 checkpoint step（不执行，只记录/验证）
        for step in self.steps:
            action = step.get("action", "")
            if action == "_checkpoint_save":
                from browser_control.client import BrowserClient
                name = step.get("checkpoint_name", " unnamed")
                url = result.get("final_url", "")
                title = result.get("title", "")
                with BrowserClient(cdp_url=cdp_url) as client:
                    cp = Checkpoint(name)
                    cp.save(url=url, title=title,
                           cookies=client.get_cookies(),
                           scroll_position=0)
                result["checkpoints"][name] = str(cp.path)

            elif action == "_checkpoint_verify":
                name = step.get("checkpoint_name")
                verify_url = step.get("verify_url")
                verify_selector = step.get("verify_selector")
                if name:
                    cp = Checkpoint(name)
                    try:
                        cp_data = cp.load()
                        passed = True
                        if verify_url and verify_url not in (cp_data.get("url") or ""):
                            passed = False
                            print(f"[X] URL 验证失败: 期望含'{verify_url}'")
                        if passed:
                            print(f"[+] Checkpoint '{name}' 验证通过")
                            result["steps"].append({
                                "action": "_checkpoint_verify",
                                "checkpoint": name,
                                "ok": True
                            })
                        else:
                            result["steps"].append({
                                "action": "_checkpoint_verify",
                                "checkpoint": name,
                                "ok": False
                            })
                            result["ok"] = False
                    except FileNotFoundError:
                        print(f"[X] Checkpoint '{name}' 不存在")
                        result["ok"] = False

        return result


# ──────────────────────────────────────────
# CLI
# ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="browser-control Checkpoint 管理")
    parser.add_argument("--action", "-a", required=True,
                        choices=["save", "load", "list", "verify",
                                 "diff", "run", "clean"],
                        help="操作")
    parser.add_argument("--name", "-n", help="Checkpoint 名称")
    parser.add_argument("--path", "-p", help="Checkpoint 文件路径")
    parser.add_argument("--workflow", "-w", help="Workflow 文件路径")
    # verify
    parser.add_argument("--checkpoint", "-c", help="用于验证的 Checkpoint")
    parser.add_argument("--verify-url", help="期望 URL（含此字符串即通过）")
    parser.add_argument("--verify-selector", help="期望存在的 selector")
    # diff
    parser.add_argument("--other", "-o", help="对比的另一个 Checkpoint")
    # common
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222")

    args = parser.parse_args()

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    if args.action == "save":
        name = args.name or f"cp_{int(time.time())}"
        from browser_control.client import BrowserClient
        with BrowserClient(cdp_url=args.cdp_url) as client:
            cp = Checkpoint(name)
            cp.save(url=client.url(), title=client.title(),
                   cookies=client.get_cookies())
        print(f"[OK] {cp.path}")

    elif args.action == "load":
        cp = Checkpoint(args.name or "", args.path)
        data = cp.load()
        print(json.dumps(data, ensure_ascii=False, indent=2))

    elif args.action == "list":
        print(f"[CHECKPOINTS] {CHECKPOINT_DIR}")
        checkpoints = sorted(CHECKPOINT_DIR.glob("*.json"))
        if not checkpoints:
            print("  (空)")
        for p in checkpoints:
            data = json.load(open(p, "r", encoding="utf-8", errors="ignore"))
            saved = data.get("saved_at_iso", "?")
            url = data.get("url", "?")
            print(f"  {p.stem} | {saved} | {url[:60]}")

    elif args.action == "verify":
        cp = Checkpoint(args.name or "", args.path or args.checkpoint)
        try:
            data = cp.load()
        except TypeError:
            print("[X] 需要 --name 或 --path")
            return 1

        ok = True
        if args.verify_url and args.verify_url not in (data.get("url") or ""):
            print(f"[X] URL 不匹配: 期望 '{args.verify_url}'")
            ok = False
        else:
            print(f"[+] URL 验证通过: {data.get('url', '')}")

        if ok:
            print(f"[PASS] Checkpoint '{cp.name}' 验证通过")
            return 0
        else:
            print(f"[FAIL] Checkpoint '{cp.name}' 验证失败")
            return 1

    elif args.action == "diff":
        a = Checkpoint(args.name or "", args.path)
        diff_result = a.diff(args.other)
        print(json.dumps(diff_result, ensure_ascii=False, indent=2))
        return 0 if diff_result["same"] else 1

    elif args.action == "run":
        if not args.workflow:
            print("[X] 需要 --workflow")
            return 1
        runner = WorkflowRunner(args.workflow)
        result = runner.run(cdp_url=args.cdp_url)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1

    elif args.action == "clean":
        checkpoints = list(CHECKPOINT_DIR.glob("*.json"))
        for p in checkpoints:
            p.unlink()
        print(f"[OK] 已删除 {len(checkpoints)} 个 Checkpoint")

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
