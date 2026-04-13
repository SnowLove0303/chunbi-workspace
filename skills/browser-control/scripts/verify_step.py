"""
三维验证器 CLI + 库
功能精准度 × 效率得分 × 成果达标率

用法:
  python verify_step.py --step check_nav --expected-url "baidu.com" --actual-url "baidu.com"
  python verify_step.py --step check_click --actual-time-ms 3200 --timeout-ms 5000
  python verify_step.py --step check_output --file-path "output/result.json"

也可用作库:
  from verify_step import StepVerifier
  v = StepVerifier("my_step")
  v.verify_functionality(...)
  v.verify_efficiency(5000, 2100)
  v.final_check()
"""
import argparse
import json
import sys
import io
import time
import hashlib
from pathlib import Path

# Windows GBK 兼容
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


class StepVerifier:
    """
    三维验证器：功能精准度 / 效率得分 / 成果达标率

    使用方式:
        v = StepVerifier("step_name")
        v.verify_functionality(selector="ok", expected_state="matched", actual_state="matched")
        v.verify_efficiency(timeout_threshold=5000, actual_time_ms=2100)
        v.verify_output(file_path="output/result.json", required_fields=["url", "data"])
        result = v.final_check()
    """

    def __init__(self, step_id: str, verbose: bool = True):
        self.step_id = step_id
        self.verbose = verbose
        self.results: dict = {}
        self._start = time.time()

    def log(self, msg: str):
        if self.verbose:
            print(f"  [{self.step_id}] {msg}")

    # ─── 1. 功能精准度 ───
    def verify_functionality(
        self,
        selector: str = None,
        expected_state: str = "matched",
        actual_state: str = "matched",
        url_expected: str = None,
        url_actual: str = None,
        cookies_expected: int = None,
        cookies_actual: int = None,
    ) -> bool:
        """
        验证功能正确性

        返回: True = 通过（>= 60分），False = 不通过
        """
        score = 100
        reasons = []

        if selector is None:
            score -= 50
            reasons.append("selector=None")

        state_ok = expected_state == actual_state
        if not state_ok:
            score -= 30
            reasons.append(f"state({expected_state}≠{actual_state})")

        url_ok = True
        if url_expected and url_expected not in (url_actual or ""):
            url_ok = False
            score -= 20
            reasons.append(f"url(期望含'{url_expected}'实际'{url_actual}')")

        if cookies_expected is not None:
            if cookies_actual is None or cookies_actual < cookies_expected:
                score -= 20
                reasons.append(f"cookies(期望>={cookies_expected}实际{cookies_actual})")

        score = max(0, score)
        self.results["functionality"] = score
        self.log(f"功能精准度: {score}/100 {'✗' if score < 60 else '✓'}"
                + (f" ({', '.join(reasons)})" if reasons else ""))
        return score >= 60

    # ─── 2. 效率得分 ───
    def verify_efficiency(self, timeout_threshold: float,
                         actual_time_ms: float) -> bool:
        """
        验证执行效率

        得分 = (超时阈值 / 实际耗时) * 100，上限100
        期望耗时越短，得分越高；超时则0分
        """
        if actual_time_ms <= 0:
            self.results["efficiency"] = 0
            self.log("效率得分: 0/100 (无效耗时)")
            return False

        if actual_time_ms > timeout_threshold:
            ratio = timeout_threshold / actual_time_ms
            score = max(0, int(ratio * 100))
        else:
            # 未超时：效率良好，按比例给分，上限100
            ratio = timeout_threshold / actual_time_ms
            score = min(100, int(ratio * 100))

        self.results["efficiency"] = score
        icon = "✓" if score >= 60 else "✗"
        self.log(f"效率得分: {score}/100 {icon} "
                f"(阈值{timeout_threshold:.0f}ms 实际{actual_time_ms:.0f}ms)")
        return score >= 60

    # ─── 3. 成果达标率 ───
    def verify_output(
        self,
        output: dict = None,
        file_path: str = None,
        required_fields: list = None,
        schema: dict = None,
        min_file_size: int = 100,
        min_extracted_fields: int = 0,
    ) -> bool:
        """
        验证输出成果

        检查: 文件存在+大小 / 必填字段 / 字段类型
        """
        file_score = 100
        field_score = 100
        schema_score = 100

        # 文件检查
        if file_path:
            p = Path(file_path)
            if not p.exists():
                file_score = 0
                self.log(f"[X] 文件不存在: {p}")
            elif p.stat().st_size < min_file_size:
                file_score = 0
                self.log(f"[X] 文件过小: {p.stat().st_size} bytes < {min_file_size}")
            else:
                self.log(f"[+] 文件正常: {p.name} ({p.stat().st_size} bytes)")

            # 如果指定了文件但没有传 output，尝试从文件加载
            if output is None and p.exists() and p.stat().st_size < 1024 * 1024:
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    if p.suffix == ".json":
                        output = json.loads(content)
                    else:
                        output = {"_raw": content}
                except Exception as e:
                    self.log(f"[!] 文件加载失败: {e}")

        # 必填字段检查
        if required_fields and output:
            found = [f for f in required_fields
                     if output and output.get(f)]
            missing = list(set(required_fields) - set(found))
            if missing:
                field_score = int(len(found) / len(required_fields) * 100)
                self.log(f"[!] 缺失字段: {missing} (完整度 {field_score}%)")
            else:
                self.log(f"[+] 字段完整: {required_fields}")

        # 提取字段数检查
        if min_extracted_fields > 0 and output:
            extracted_keys = [k for k in output.keys()
                             if k not in ("ok", "steps", "final_url", "title")]
            if len(extracted_keys) < min_extracted_fields:
                self.log(f"[!] 提取字段不足: {len(extracted_keys)} < {min_extracted_fields}")

        # 字段类型检查
        if schema and output:
            type_errors = []
            for field, expected_type in schema.items():
                if field not in output:
                    continue
                actual = type(output[field]).__name__
                if expected_type not in (actual, "NoneType"):
                    type_errors.append(f"{field}(期望{expected_type}实际{actual})")
                    schema_score -= 20
            if type_errors:
                self.log(f"[!] 类型错误: {type_errors}")

        output_score = min(file_score, max(0, field_score),
                          max(0, schema_score))
        self.results["output"] = output_score
        icon = "✓" if output_score >= 60 else "✗"
        self.log(f"成果达标率: {output_score}/100 {icon}")
        return output_score >= 60

    # ─── 4. 截图验证 ───
    def verify_screenshot(self, path: str,
                          expected_size_kb: int = 5,
                          expected_width: int = None,
                          expected_height: int = None) -> bool:
        """验证截图质量"""
        p = Path(path)
        if not p.exists():
            self.log(f"[X] 截图不存在: {path}")
            self.results["screenshot"] = 0
            return False

        size_kb = p.stat().st_size / 1024
        score = 100

        if size_kb < expected_size_kb:
            score -= 50
            self.log(f"[!] 截图过小: {size_kb:.1f}KB < {expected_size_kb}KB")

        # 尺寸检查（如果有 PIL）
        if expected_width or expected_height:
            try:
                from PIL import Image
                img = Image.open(p)
                w, h = img.size
                if expected_width and abs(w - expected_width) > 50:
                    score -= 25
                    self.log(f"[!] 宽度不符: {w} vs 期望{expected_width}")
                if expected_height and abs(h - expected_height) > 50:
                    score -= 25
                    self.log(f"[!] 高度不符: {h} vs 期望{expected_height}")
                img.close()
            except ImportError:
                pass  # 无 PIL 就跳过

        self.results["screenshot"] = score
        self.log(f"截图验证: {score}/100 ({size_kb:.1f}KB)")
        return score >= 60

    # ─── 5. 综合判定 ───
    def final_check(self) -> dict:
        """
        综合三个维度打分，返回判定结果

        PASS   : 所有参与维度 >= 60
        RETRY  : 部分 < 60 但无维度 < 40
        ABORT  : 任何维度 < 40
        PASS*  : 无数据（降级通过）
        """
        func = self.results.get("functionality", 0)
        eff = self.results.get("efficiency", 0)
        out = self.results.get("output", 0)
        shot = self.results.get("screenshot", 0)

        measured = [(n, v) for n, v in [
            ("功能", func), ("效率", eff), ("成果", out), ("截图", shot)
        ] if v > 0]

        scores_str = "/".join(f"{n}{v:.0f}" for n, v in measured)
        elapsed = time.time() - self._start

        if not measured:
            verdict = "PASS*"
            self.log(f"[PASS*] 无验证数据（降级通过，耗时{elapsed:.1f}s）")
        elif all(v >= 60 for _, v in measured):
            verdict = "PASS"
            self.log(f"[PASS] {scores_str} (耗时{elapsed:.1f}s)")
        elif any(v < 40 for _, v in measured):
            verdict = "ABORT"
            self.log(f"[ABORT] {scores_str} (耗时{elapsed:.1f}s)")
        else:
            verdict = "RETRY"
            self.log(f"[RETRY] {scores_str} (耗时{elapsed:.1f}s)")

        return {
            "verdict": verdict,
            "functionality": func,
            "efficiency": eff,
            "output": out,
            "screenshot": shot,
            "elapsed_s": round(elapsed, 2),
            "scores": dict(measured),
        }

    def to_json(self) -> str:
        return json.dumps(self.results, ensure_ascii=False, indent=2)


# ──────────────────────────────────────────
# CLI
# ──────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="三维验证器 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--step", required=True, help="步骤名称")
    parser.add_argument("--expected-url", help="期望 URL（含此字符串即通过）")
    parser.add_argument("--actual-url", help="实际 URL")
    parser.add_argument("--expected-state", default="matched")
    parser.add_argument("--actual-state", default="matched")
    parser.add_argument("--selector", help="selector 结果（None=未命中）")
    parser.add_argument("--timeout-ms", type=int, default=5000,
                       help="超时阈值(ms)")
    parser.add_argument("--actual-time-ms", type=float,
                       help="实际耗时(ms)")
    parser.add_argument("--file-path", "--file", "-f",
                       help="输出文件路径")
    parser.add_argument("--required-fields",
                       help="逗号分隔的必填字段")
    parser.add_argument("--min-file-size", type=int, default=100,
                       help="文件最小字节数")
    parser.add_argument("--output-json", help="JSON 输出文件（会被 --file-path 替代）")
    parser.add_argument("--quiet", "-q", action="store_true")

    args = parser.parse_args()
    v = StepVerifier(args.step, verbose=not args.quiet)

    # 功能验证
    if args.expected_url or args.selector is not None:
        v.verify_functionality(
            selector=args.selector,
            expected_state=args.expected_state,
            actual_state=args.actual_state,
            url_expected=args.expected_url,
            url_actual=args.actual_url,
        )

    # 效率验证
    if args.actual_time_ms is not None:
        v.verify_efficiency(args.timeout_ms, args.actual_time_ms)

    # 成果验证
    if args.file_path or args.output_json:
        out_file = args.file_path or args.output_json
        required = args.required_fields.split(",") if args.required_fields else None
        v.verify_output(
            file_path=out_file,
            required_fields=required,
            min_file_size=args.min_file_size,
        )

    result = v.final_check()
    print(json.dumps(result, ensure_ascii=False, indent=2))

    exit_code = {"PASS": 0, "PASS*": 0, "RETRY": 1, "ABORT": 2}.get(
        result["verdict"], 0)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
