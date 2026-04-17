import json, sys
sys.path.insert(0, r'F:\openclaw1\.openclaw\workspace\skills\browser-control')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
with open(r'F:\openclaw1\.openclaw\workspace\skills\browser-control\output\workflow_result.json', encoding='utf-8', errors='replace') as f:
    d = json.load(f)
for i, s in enumerate(d['steps']):
    print(f'Step {i+1}: {s.get("value", "")[:200]}')