"""获取创建弹窗表单字段"""
import sys
sys.path.insert(0, r"F:\openclaw1\.openclaw\workspace\skills\browser-control")
from browser_control.client import run_actions
import json

r = run_actions([
    {"action": "eval_js", "script": "(function(){var result=[];document.querySelectorAll('[class*=modal] input,[class*=modal] textarea,[class*=drawer] input,[class*=drawer] textarea,[class*=dialog] input,[class*=dialog] textarea').forEach(function(i){var p=i.placeholder||'';var t=i.type||i.tagName;result.push({p:p,t:t,id:i.id,n:i.name,w:i.offsetWidth,h:i.offsetHeight,vis:i.offsetWidth>0&&i.offsetHeight>0});});return JSON.stringify(result);})();"}
], cdp_url="http://127.0.0.1:9222")

try:
    d = json.loads(r["steps"][0].get("value","{}"))
    print(json.dumps(d, ensure_ascii=False, indent=2))
except:
    print("raw:", r["steps"][0].get("value",""))
