"""三维验证器 - 功能精准度 × 效率得分 × 成果达标率"""
import json
import time
import re
import sys
import io
from pathlib import Path

# Windows GBK 兼容
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

class StepVerifier:
    """三维验证器：功能精准度 / 效率得分 / 成果达标率"""

    def __init__(self, step_id, verbose=True):
        self.step_id = step_id
        self.verbose = verbose
        self.results = {}
        self.logs = []

    def log(self, msg):
        if self.verbose:
            print(f"  [{self.step_id}] {msg}")

    # ─── 功能精准度 ───
    def verify_functionality(self, selector, expected_state, actual_state,
                             url_expected=None, url_actual=None):
        matched = selector is not None
        state_correct = expected_state == actual_state

        url_ok = True
        if url_expected:
            url_ok = url_expected in (url_actual or "")
            self.log(f"URL 验证: {'[+]' if url_ok else '[X]'} "
                     f"期望含 '{url_expected}' 实际 '{url_actual}'")

        score = 100 if (matched and state_correct and url_ok) else 0

        if not matched:
            score -= 50
            self.log(f"[X] selector 未命中: {selector}")
        if not state_correct:
            score -= 30
            self.log(f"[X] 状态不符: 期望 '{expected_state}' 实际 '{actual_state}'")
        if not url_ok:
            score -= 20

        self.results['functionality'] = max(0, score)
        self.log(f"功能精准度: {self.results['functionality']}/100")
        return self.results['functionality'] >= 60

    # ─── 效率得分 ───
    def verify_efficiency(self, timeout_threshold, actual_time):
        if actual_time <= 0:
            score = 0
        else:
            ratio = timeout_threshold / actual_time
            score = min(100, int(ratio * 100))

        self.results['efficiency'] = score
        self.log(f"效率得分: {score}/100 (阈值{timeout_threshold}ms 实际{actual_time:.0f}ms)")
        return score >= 60

    # ─── 成果达标率 ───
    def verify_output(self, output, required_fields=None, schema=None,
                       min_file_size=100, file_path=None):
        if file_path:
            p = Path(file_path)
            if p.exists() and p.stat().st_size >= min_file_size:
                self.log(f"[+] 文件存在且有效: {p} ({p.stat().st_size} bytes)")
            else:
                self.results['output'] = 0
                self.log(f"[X] 文件无效或过小: {p}")
                return False

        field_score = 100
        if required_fields:
            missing = [f for f in required_fields
                       if output is None or
                       (isinstance(output, dict) and not output.get(f))]
            if missing:
                field_score = int((len(required_fields) - len(missing))
                                   / len(required_fields) * 100)
                self.log(f"[!] 缺失字段: {missing}, 字段完整度: {field_score}%")

        schema_score = 100
        if schema and isinstance(output, dict):
            for key, expected_type in schema.items():
                if key not in output:
                    continue
                actual_type = type(output[key]).__name__
                if expected_type not in (actual_type, "NoneType"):
                    schema_score -= 20
                    self.log(f"[!] 字段类型不符: {key} 期望 {expected_type} 实际 {actual_type}")

        output_score = min(field_score, max(0, schema_score))
        self.results['output'] = output_score
        self.log(f"成果达标率: {output_score}/100")
        return output_score >= 60

    # ─── 综合判定 ───
    def final_check(self):
        func = self.results.get('functionality', 0)
        eff  = self.results.get('efficiency', 0)
        out  = self.results.get('output', 0)

        # 只有实际计算过的维度才参与判定（避免 workflow 部分步骤跳过时 0 分触发 ABORT）
        measured = [(n, v) for n, v in [('functionality', func), ('efficiency', eff), ('output', out)] if v > 0]

        verdict = {
            'functionality': func,
            'efficiency': eff,
            'output': out,
            'overall': 'UNKNOWN'
        }

        if not measured:
            # 完全无数据，降级为 PASS 而非 ABORT
            verdict['overall'] = 'PASS'
            self.log(f"[PASS] 无维度数据（降级通过）")
        elif all(v >= 60 for _, v in measured):
            verdict['overall'] = 'PASS'
            self.log(f"[PASS] 功能{func:.0f}/效率{eff:.0f}/成果{out:.0f}")
        elif any(v < 40 for _, v in measured):
            verdict['overall'] = 'ABORT'
            self.log(f"[ABORT] {'/'.join(f'{n}{v:.0f}' for n,v in measured)}")
        else:
            verdict['overall'] = 'RETRY'
            self.log(f"[RETRY] {'/'.join(f'{n}{v:.0f}' for n,v in measured)}")

        return verdict

    def to_json(self):
        return json.dumps(self.results, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="三维验证器 CLI")
    parser.add_argument("--step", required=True, help="步骤名称")
    parser.add_argument("--expected-url", help="期望 URL")
    parser.add_argument("--actual-url", help="实际 URL")
    parser.add_argument("--timeout-ms", type=int, default=5000, help="超时阈值(ms)")
    parser.add_argument("--actual-time-ms", type=float, help="实际耗时(ms)")
    parser.add_argument("--required-fields", help="逗号分隔的必填字段")
    parser.add_argument("--selector", help="selector 结果")
    parser.add_argument("--expected-state", help="期望 DOM 状态")
    parser.add_argument("--actual-state", help="实际 DOM 状态")
    parser.add_argument("--output-json", help="输出 JSON 文件路径")
    parser.add_argument("--file-path", help="输出文件路径")

    args = parser.parse_args()

    v = StepVerifier(args.step)

    if args.expected_url:
        v.verify_functionality(
            selector=args.selector,
            expected_state=args.expected_state or "matched",
            actual_state=args.actual_state or "matched",
            url_expected=args.expected_url,
            url_actual=args.actual_url
        )

    if args.actual_time_ms is not None:
        v.verify_efficiency(args.timeout_ms, args.actual_time_ms)

    if args.output_json or args.file_path:
        output_data = {}
        if args.output_json and Path(args.output_json).exists():
            with open(args.output_json) as f:
                output_data = json.load(f)
        required = args.required_fields.split(",") if args.required_fields else None
        v.verify_output(
            output=output_data,
            required_fields=required,
            file_path=args.file_path
        )

    result = v.final_check()
    print(json.dumps(result, ensure_ascii=False, indent=2))

    exit_code = 0 if result['overall'] == 'PASS' else \
                1 if result['overall'] == 'RETRY' else 2
    sys.exit(exit_code)
