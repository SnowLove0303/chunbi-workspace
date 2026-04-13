"""Checkpoint 持久化 - 浏览器精准控制闭环方案配套"""
import json
import os
import sys
import io
from datetime import datetime

# Windows GBK 兼容
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

class Checkpoint:
    def __init__(self, checkpoint_dir="./checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)

    def save(self, step_name, data=None):
        """保存检查点"""
        checkpoint = {
            "step": step_name,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        path = os.path.join(self.checkpoint_dir, f"{step_name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2)
        print(f"[SAVE] Checkpoint saved: {step_name}")

    def load(self, step_name):
        """恢复检查点"""
        path = os.path.join(self.checkpoint_dir, f"{step_name}.json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        return None

    def exists(self, step_name):
        """检查点是否存在"""
        return os.path.exists(os.path.join(self.checkpoint_dir, f"{step_name}.json"))

    def get_last_step(self):
        """获取最后一个已完成的步骤"""
        checkpoints = []
        for fname in os.listdir(self.checkpoint_dir):
            if fname.endswith(".json"):
                step_name = fname[:-5]
                cp = self.load(step_name)
                if cp:
                    checkpoints.append((step_name, cp["timestamp"]))

        if not checkpoints:
            return None

        checkpoints.sort(key=lambda x: x[1], reverse=True)
        return checkpoints[0][0]

    def list_all(self):
        """列出所有检查点"""
        return [f[:-5] for f in os.listdir(self.checkpoint_dir) if f.endswith(".json")]

if __name__ == "__main__":
    cp = Checkpoint()

    if len(sys.argv) < 2:
        all_cp = cp.list_all()
        print(f"[LIST] 共 {len(all_cp)} 个检查点:")
        for name in all_cp:
            data = cp.load(name)
            print(f"  - {name} @ {data['timestamp']}")
    else:
        step = sys.argv[1]
        data = cp.load(step)
        if data:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"[X] 未找到检查点: {step}")
