"""文件夹程序重复度审查脚本 - 通用浏览器控制框架配套
扫描目标目录，发现功能重复的程序，建议复用而非新建
"""
import os
import re
import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher
import importlib.util


# ─── 重复度阈值 ───
SIMILARITY_THRESHOLD_HIGH = 0.80   # ≥80% → 强制复用
SIMILARITY_THRESHOLD_MED = 0.60    # ≥60% → 审查合并
SIMILARITY_THRESHOLD_LOW = 0.40    # ≥40% → 可选复用


def levenshtein_distance(s1: str, s2: str) -> int:
    """计算两个字符串的编辑距离"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def similarity_ratio(s1: str, s2: str) -> float:
    """两个字符串的相似度（0-1）"""
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    return SequenceMatcher(None, s1, s2).ratio()


def file_content_hash(file_path: Path) -> str:
    """文件内容 MD5（只对 .py 等代码文件）"""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        return hashlib.md5(content.encode("utf-8", errors="ignore")).hexdigest()
    except Exception:
        return ""


def extract_keywords(code: str) -> set:
    """从代码中提取关键词（函数名、类名、注释关键字）"""
    keywords = set()

    # 函数名
    funcs = re.findall(r'def\s+(\w+)\s*\(', code)
    keywords.update(funcs)

    # 类名
    classes = re.findall(r'class\s+(\w+)\s*[\(:]', code)
    keywords.update(classes)

    # docstring 关键词
    docstrings = re.findall(r'"""(.*?)"""', code, re.DOTALL)
    for doc in docstrings:
        words = re.findall(r'\b[a-zA-Z]{4,}\b', doc.lower())
        keywords.update(words)

    # 行内注释关键词
    comments = re.findall(r'#\s*(.+)', code)
    for comment in comments:
        words = re.findall(r'\b[a-zA-Z]{4,}\b', comment.lower())
        keywords.update(words)

    # 过滤 Python 保留字
    reserved = {"def", "class", "import", "from", "return", "if", "else", "elif",
               "for", "while", "try", "except", "with", "as", "lambda", "yield",
               "True", "False", "None", "self", "print", "range", "len", "list",
               "dict", "str", "int", "float", "set", "tuple"}
    keywords -= reserved
    return keywords


def analyze_file(file_path: Path) -> dict:
    """分析单个文件，返回结构和签名"""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        content = ""

    return {
        "path": str(file_path),
        "name": file_path.name,
        "size": file_path.stat().st_size if file_path.is_file() else 0,
        "hash": file_content_hash(file_path),
        "keywords": extract_keywords(content),
        "content_sample": content[:500],  # 前500字符用于内容对比
        "func_count": len(re.findall(r'def\s+\w+\s*\(', content)),
        "imports": set(re.findall(r'^(?:import|from)\s+([\w.]+)', content, re.MULTILINE)),
    }


def compare_two(a: dict, b: dict) -> dict:
    """对比两个文件，返回多维度重复度分析"""
    scores = {}

    # 1. 文件名相似度
    scores["name_similarity"] = similarity_ratio(a["name"], b["name"])

    # 2. 关键词重叠度（Jaccard）
    common_kw = a["keywords"] & b["keywords"]
    union_kw = a["keywords"] | b["keywords"]
    scores["keyword_jaccard"] = len(common_kw) / len(union_kw) if union_kw else 0

    # 3. 核心函数完全匹配
    common_funcs = a["keywords"] & b["keywords"]
    # 过滤掉非函数名的词（取至少包含一个括号的）
    func_overlap = len([k for k in common_funcs if "(" in k or k in ["def", "class"]])
    scores["func_overlap"] = min(1.0, func_overlap / max(len(a["keywords"]), 1))

    # 4. import 模块重叠度（Jaccard）
    common_imp = a["imports"] & b["imports"]
    union_imp = a["imports"] | b["imports"]
    scores["import_jaccard"] = len(common_imp) / len(union_imp) if union_imp else 0

    # 5. 内容相似度（Levenshtein 距离）
    content_a = a["content_sample"]
    content_b = b["content_sample"]
    scores["content_similarity"] = similarity_ratio(content_a, content_b)

    # 综合相似度（加权平均）
    composite = (
        scores["name_similarity"] * 0.15 +
        scores["keyword_jaccard"] * 0.25 +
        scores["content_similarity"] * 0.35 +
        scores["import_jaccard"] * 0.15 +
        scores["func_overlap"] * 0.10
    )
    scores["composite"] = round(composite, 4)

    return scores


class DuplicateScanner:
    """重复度扫描器"""

    def __init__(self, scan_dir: str, extensions=None):
        self.scan_dir = Path(scan_dir)
        self.extensions = extensions or [".py", ".js", ".ts", ".yaml", ".yml", ".sh"]
        self.files = []

    def scan(self) -> list:
        """扫描目录下所有代码文件"""
        for f in self.scan_dir.rglob("*"):
            if f.is_file() and f.suffix in self.extensions:
                # 跳过自身和 __pycache__
                if "__pycache__" in str(f) or f.name in ["scan_duplicates.py", "check_code.py"]:
                    continue
                self.files.append(analyze_file(f))
        return self.files

    def compare_all(self) -> list:
        """两两对比所有文件"""
        results = []
        n = len(self.files)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = self.files[i], self.files[j]
                scores = compare_two(a, b)
                if scores["composite"] >= SIMILARITY_THRESHOLD_LOW:
                    results.append({
                        "file_a": a["path"],
                        "file_b": b["path"],
                        "scores": scores,
                        "decision": self.decide(scores["composite"])
                    })
        # 按相似度排序
        results.sort(key=lambda x: x["scores"]["composite"], reverse=True)
        return results

    def decide(self, score: float) -> dict:
        """根据分数给出决策"""
        if score >= SIMILARITY_THRESHOLD_HIGH:
            return {
                "level": "[E] 高度重复",
                "action": "强制复用，不得新建",
                "threshold": SIMILARITY_THRESHOLD_HIGH
            }
        elif score >= SIMILARITY_THRESHOLD_MED:
            return {
                "level": "[W] 中度重复",
                "action": "审查是否可合并，再决定",
                "threshold": SIMILARITY_THRESHOLD_MED
            }
        else:
            return {
                "level": "[I] 低度相似",
                "action": "可选复用，视情况决定",
                "threshold": SIMILARITY_THRESHOLD_LOW
            }

    def check_new_file(self, new_file_path: str) -> dict:
        """检查新文件是否与现有文件重复"""
        new_p = Path(new_file_path)
        if not new_p.exists():
            return {"error": f"文件不存在: {new_file_path}"}

        new_analysis = analyze_file(new_p)
        results = []

        for existing in self.files:
            scores = compare_two(new_analysis, existing)
            if scores["composite"] >= SIMILARITY_THRESHOLD_LOW:
                results.append({
                    "existing_file": existing["path"],
                    "new_file": new_file_path,
                    "scores": scores,
                    "decision": self.decide(scores["composite"])
                })

        results.sort(key=lambda x: x["scores"]["composite"], reverse=True)
        return {
            "new_file": new_file_path,
            "matches": results,
            "all_clear": len(results) == 0
        }

    def generate_report(self, comparisons: list) -> str:
        """生成文本报告"""
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"[FIND] 重复度扫描报告")
        lines.append(f"   目录: {self.scan_dir}")
        lines.append(f"   文件数: {len(self.files)}")
        lines.append(f"{'='*60}\n")

        if not comparisons:
            lines.append("[+] 未发现明显重复（相似度 < 40% 的已过滤）\n")
            return "\n".join(lines)

        for item in comparisons:
            s = item["scores"]
            d = item["decision"]
            lines.append(f"{d['level']}  相似度: {s['composite']:.1%}")
            lines.append(f"  文件 A: {item['file_a']}")
            lines.append(f"  文件 B: {item['file_b']}")
            lines.append(f"  决策: {d['action']}")
            lines.append(f"  细分: "
                         f"文件名={s['name_similarity']:.0%} | "
                         f"关键词={s['keyword_jaccard']:.0%} | "
                         f"内容={s['content_similarity']:.0%} | "
                         f"依赖={s['import_jaccard']:.0%}")
            lines.append("")

        return "\n".join(lines)


def scan_directory(dir_path: str, new_file_path: str = None) -> dict:
    """
    主扫描入口
    - 扫描 dir_path 下所有代码文件
    - 如指定 new_file_path，则额外检查该文件是否重复
    """
    scanner = DuplicateScanner(dir_path)
    scanner.scan()

    results = {
        "scan_dir": str(scanner.scan_dir),
        "file_count": len(scanner.files),
        "files": [{"name": f["name"], "path": f["path"], "func_count": f["func_count"]} for f in scanner.files],
        "timestamp": datetime.now().isoformat()
    }

    # 两两对比
    comparisons = scanner.compare_all()
    results["comparisons"] = comparisons
    results["high_duplicates"] = [c for c in comparisons if "高度重复" in c["decision"]["level"]]
    results["medium_duplicates"] = [c for c in comparisons if "中度重复" in c["decision"]["level"]]

    # 新文件检查
    if new_file_path:
        new_check = scanner.check_new_file(new_file_path)
        results["new_file_check"] = new_check

    return results


def print_report(results: dict):
    """打印人类可读报告"""
    scanner = DuplicateScanner(results["scan_dir"])
    report = scanner.generate_report(results.get("comparisons", []))
    print(report)

    # 新文件检查结果
    if "new_file_check" in results:
        nc = results["new_file_check"]
        if "error" in nc:
            print(f"[X] {nc['error']}")
        elif nc.get("all_clear"):
            print(f"[+] 新文件检查通过，未发现重复\n")
        else:
            print(f"[!]  新文件 '{nc['new_file']}' 存在以下相似文件:\n")
            for match in nc["matches"]:
                s = match["scores"]
                d = match["decision"]
                print(f"  {d['level']} {s['composite']:.1%} → {match['existing_file']}")
                print(f"    建议: {d['action']}\n")

    # 汇总
    high = len(results.get("high_duplicates", []))
    med = len(results.get("medium_duplicates", []))
    if high > 0:
        print(f"[E] 警告: {high} 对高度重复文件（≥80%）— 必须复用\n")
    if med > 0:
        print(f"[W] 注意: {med} 对中度重复文件（≥60%）— 建议审查\n")


# ─── CLI ───
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="文件夹程序重复度审查")
    parser.add_argument("dir", nargs="?", default=None, help="扫描目录（默认: 脚本所在目录）")
    parser.add_argument("--check", "-c", metavar="FILE", help="检查新文件是否与目录内程序重复")
    parser.add_argument("--json", "-j", action="store_true", help="JSON 输出")
    parser.add_argument("--threshold", "-t", type=float, default=0.4,
                       metavar="0.0-1.0", help="相似度阈值（默认 0.4）")
    args = parser.parse_args()

    global_threshold = args.threshold

    # 扫描目录
    scan_dir = args.dir if args.dir else str(Path(__file__).parent)
    if not Path(scan_dir).exists():
        print(f"[X] 目录不存在: {scan_dir}")
        sys.exit(1)

    results = scan_directory(scan_dir, args.check)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print_report(results)

    # 退出码
    high = len(results.get("high_duplicates", []))
    if high > 0:
        sys.exit(2)  # 高度重复
    sys.exit(0)
