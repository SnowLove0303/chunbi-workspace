"""保存工作流执行结果到 JSON"""
import json, sys, os
from pathlib import Path

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else ""
    screenshot = sys.argv[2] if len(sys.argv) > 2 else ""
    status = sys.argv[3] if len(sys.argv) > 3 else "done"

    result = {"url": url, "screenshot": screenshot, "status": status}

    output_path = Path(__file__).parent.parent / "output" / "result.json"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Result saved to {output_path}")
