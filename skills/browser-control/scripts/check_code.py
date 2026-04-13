"""程序代码审核脚本 - 通用浏览器控制框架配套
在脚本进入工作区前，自动审核代码质量和安全
"""
import os
import re
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

# ─── 严重模式：[E] 严重 / [W] 警告 / [I] 提示 ───
ISSUE_LEVEL = {"ERROR": "[E]", "WARN": "[W]", "INFO": "[I]"}


class CodeAuditor:
    """代码审核器"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.issues = []
        self.passed = True

    def audit(self) -> dict:
        """执行全量审核"""
        if not self.file_path.exists():
            self.add_issue("ERROR", f"文件不存在: {self.file_path}")
            return self.result()

        ext = self.file_path.suffix.lower()
        if ext not in (".py", ".js", ".ts", ".yaml", ".yml", ".sh", ".ps1"):
            self.add_issue("INFO", f"跳过非代码文件: {ext}")

        code = self.read_code()

        self.check_syntax(code, ext)
        self.check_hardcoded_secrets(code)
        self.check_dangerous_commands(code)
        self.check_path_safety(code)
        self.check_timeout(code)
        self.check_exception_handling(code)
        self.check_dependencies(code)
        self.check_print_in_production(code)

        return self.result()

    def read_code(self) -> str:
        encodings = ["utf-8", "gbk", "latin-1"]
        for enc in encodings:
            try:
                return self.file_path.read_text(encoding=enc)
            except UnicodeDecodeError:
                continue
        return ""

    # ─── 检查项 ───

    def check_syntax(self, code: str, ext: str):
        """语法检查"""
        if ext == ".py":
            try:
                subprocess.run(
                    ["python", "-m", "py_compile", str(self.file_path)],
                    capture_output=True, timeout=10
                )
                self.add_issue("INFO", "Python 语法检查通过")
            except subprocess.TimeoutExpired:
                self.add_issue("ERROR", "语法检查超时")
            except FileNotFoundError:
                self.add_issue("WARN", "python 未在 PATH 中，跳过语法检查")
            else:
                result = subprocess.run(
                    ["python", "-m", "py_compile", str(self.file_path)],
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    self.add_issue("ERROR", f"Python 语法错误: {result.stderr[:200]}")

    def check_hardcoded_secrets(self, code: str):
        """检查硬编码凭证（[E] 严重）"""
        secret_patterns = [
            (r'["\']api[_-]?key["\']\s*[:=]\s*["\'][^"\']{8,}["\']', "硬编码 API Key"),
            (r'["\']password["\']\s*[:=]\s*["\'][^"\']+["\']', "硬编码密码"),
            (r'["\']secret["\']\s*[:=]\s*["\'][^"\']+["\']', "硬编码 secret"),
            (r'["\']token["\']\s*[:=]\s*["\'][^"\']+["\']', "硬编码 token"),
            (r'Bearer\s+[A-Za-z0-9_-]{20,}', "硬编码 Bearer Token"),
            (r'sk-[A-Za-z0-9]{20,}', "疑似 OpenAI/GitHub Key"),
            (r'ghp_[A-Za-z0-9]{36}', "疑似 GitHub Token"),
        ]
        for pattern, name in secret_patterns:
            matches = re.findall(pattern, code, re.IGNORECASE)
            if matches:
                self.add_issue("ERROR", f"[E] 严重: {name} — 必须移至环境变量或配置文件")

    def check_dangerous_commands(self, code: str):
        """检查危险系统命令（[E] 严重）"""
        dangerous = [
            (r'rm\s+-rf\s+/', "危险: rm -rf /（强制删除根目录）"),
            (r'rm\s+-rf\s+\*', "危险: rm -rf *（强制删除当前目录）"),
            (r'del\s+/[fqs]', "危险: del 强制删除命令"),
            (r'format\s+[a-z]:', "危险: format 格式化命令"),
            (r'>?\s*/dev/sd[a-z]', "危险: 直接写设备文件"),
            (r'curl\s+\|?\s*sh', "危险: curl|sh 远程执行"),
            (r'wget\s+.*\|\s*sh', "危险: wget|sh 远程执行"),
            (r'shutdown', "危险: shutdown 命令"),
            (r'mkfs', "危险: mkfs 格式化命令"),
        ]
        for pattern, name in dangerous:
            if re.search(pattern, code, re.IGNORECASE):
                self.add_issue("ERROR", f"[E] 严重: {name}")

    def check_path_safety(self, code: str):
        """检查路径安全性（[W] 警告）"""
        # 检查是否有硬编码的 Windows 盘符路径在字符串中（相对路径更安全）
        hardcoded_absolute = re.findall(r'["\'][A-Z]:\\[^"\']+["\']', code)
        if hardcoded_absolute:
            # 不过滤常见系统路径
            filtered = [p for p in hardcoded_absolute
                        if not any(s in p for s in ["Program Files", "Windows", "Users"])]
            if filtered:
                self.add_issue("WARN", f"存在硬编码绝对路径，建议用 pathlib.Path 或相对路径: {filtered[:2]}")

        # 检查是否缺少 Path/posixpath 处理
        if "open(" in code and "Path(" not in code and "os.path" not in code:
            # 简单字符串拼接的文件操作是危险信号
            open_calls = re.findall(r'\bopen\s*\([^)]+["\'][^"\']+["\']', code)
            if open_calls:
                self.add_issue("WARN", f"检测到 open() 调用，建议使用 pathlib.Path 或 os.path 构建路径")

    def check_timeout(self, code: str):
        """检查超时保护（[W] 警告）"""
        if "subprocess.run" in code or "subprocess.Popen" in code:
            if "timeout" not in code:
                self.add_issue("WARN", "subprocess 调用缺少 timeout 参数，可能导致进程无限等待")

        if "requests." in code:
            if "timeout=" not in code:
                self.add_issue("WARN", "requests 调用缺少 timeout 参数")

    def check_exception_handling(self, code: str):
        """检查异常处理（[W] 警告）"""
        # 找出所有 try 块
        try_blocks = re.findall(r'try\s*:(.*?)(?:except|finally|else)', code, re.DOTALL)
        bare_excepts = re.findall(r'except\s*:', code)

        # 关键操作列表（没有 except 的是危险的）
        critical_ops = ["open(", "subprocess.", "requests.", "socket.", "connect("]
        has_try = bool(try_blocks)
        has_bare_except = bool(bare_excepts)

        if not has_try:
            for op in critical_ops:
                if op in code:
                    self.add_issue("WARN", f"关键操作 '{op}' 缺少 try/except 保护")
                    break

        if has_bare_except and not any("Exception" in e or "Error" in e for e in bare_excepts):
            self.add_issue("WARN", "存在 bare except 子句（except:），建议改为 except Exception:")

    def check_dependencies(self, code: str):
        """检查依赖记录（[I] 提示）"""
        # 提取 import 语句
        imports = re.findall(r'^(?:import|from)\s+([\w.]+)', code, re.MULTILINE)
        stdlib = {"os", "sys", "subprocess", "json", "re", "time", "datetime",
                  "pathlib", "socket", "platform", "shutil", "tempfile",
                  "argparse", "collections", "itertools", "functools"}

        external = set()
        for imp in imports:
            top = imp.split(".")[0]
            if top not in stdlib:
                external.add(top)

        if external:
            self.add_issue("INFO", f"检测到外部依赖: {sorted(external)} — 需确认已记录在 requirements.txt")

    def check_print_in_production(self, code: str):
        """检查生产代码中的 print（[I] 提示）"""
        if "print(" in code and "logging" not in code:
            print_count = len(re.findall(r'\bprint\s*\(', code))
            if print_count > 3:
                self.add_issue("INFO", f"发现 {print_count} 处 print，建议改用 logging 模块")

    # ─── 结果处理 ───

    def add_issue(self, level: str, message: str):
        self.issues.append({"level": level, "message": message})
        if level == "ERROR":
            self.passed = False

    def result(self) -> dict:
        errors = [i for i in self.issues if i["level"] == "ERROR"]
        warns = [i for i in self.issues if i["level"] == "WARN"]
        infos = [i for i in self.issues if i["level"] == "INFO"]

        return {
            "file": str(self.file_path),
            "passed": self.passed,
            "error_count": len(errors),
            "warn_count": len(warns),
            "info_count": len(infos),
            "issues": self.issues,
            "summary": self.passed,
            "timestamp": datetime.now().isoformat()
        }


def audit_file(file_path: str) -> dict:
    auditor = CodeAuditor(file_path)
    return auditor.audit()


def audit_directory(dir_path: str, pattern="*.py") -> list:
    """批量审核目录下所有匹配文件"""
    results = []
    dir_p = Path(dir_path)
    for f in dir_p.rglob(pattern):
        # 跳过 __pycache__ 和 .pyc
        if "__pycache__" in str(f) or f.name.endswith(".pyc"):
            continue
        result = audit_file(str(f))
        results.append(result)
    return results


def print_report(result: dict):
    """格式化打印审核报告"""
    icon = "[+]" if result["passed"] else "[X]"
    print(f"\n{'='*50}")
    print(f"{icon} 审核报告: {result['file']}")
    print(f"{'='*50}")

    for issue in result["issues"]:
        lvl_icon = ISSUE_LEVEL.get(issue["level"], "?")
        print(f"  {lvl_icon} [{issue['level']:5s}] {issue['message']}")

    summary = (f"[+] 通过 "
               f"| [E] 错误 {result['error_count']} "
               f"| [W] 警告 {result['warn_count']} "
               f"| [I] 提示 {result['info_count']}")
    print(f"\n  {summary}")
    return result["passed"]


# ─── CLI ───
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="程序代码审核")
    parser.add_argument("path", nargs="?", help="文件或目录路径")
    parser.add_argument("--pattern", "-p", default="*.py", help="目录模式（默认 *.py）")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    parser.add_argument("--strict", "-s", action="store_true", help="严格模式：警告也导致非0退出")
    args = parser.parse_args()

    if not args.path:
        # 审核自身目录下的所有代码
        base = Path(__file__).parent
        results = audit_directory(str(base), args.pattern)
    else:
        p = Path(args.path)
        if p.is_file():
            results = [audit_file(str(p))]
        else:
            results = audit_directory(str(p), args.pattern)

    # 打印报告
    all_passed = True
    for r in results:
        ok = print_report(r)
        if not ok:
            all_passed = False

    # 汇总
    total_errors = sum(r["error_count"] for r in results)
    total_warns = sum(r["warn_count"] for r in results)

    print(f"\n[STATS] 汇总: {len(results)} 个文件, "
          f"[E] {total_errors} 错误, [W] {total_warns} 警告")

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))

    # 退出码
    if not all_passed:
        sys.exit(1)
    if args.strict and total_warns > 0:
        sys.exit(1)
    sys.exit(0)
