"""飞书开发者后台导航测试"""
import sys
sys.path.insert(0, r"F:\openclaw1\.openclaw\workspace\skills\browser-control")
from browser_control.client import run_actions

r = run_actions([
    {"action": "nav", "url": "https://open.feishu.cn/app"},
    {"action": "wait_timeout", "ms": 3000},
    {"action": "screenshot", "path": r"F:\openclaw1\.openclaw\workspace\skills\browser-control\screenshots\feishu_dev_console.png", "full_page": False},
], cdp_url="http://127.0.0.1:9222")

print("URL:", r["final_url"])
print("Title:", r["title"])
print("Step OK:", r["steps"][0].get("ok"))
print("Screenshot:", r["screenshots"])
