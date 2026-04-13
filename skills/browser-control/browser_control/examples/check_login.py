import json
with open(r'F:\openclaw1\.openclaw\workspace\skills\browser-control\output\workflow_result.json', encoding='utf-8', errors='replace') as f:
    d = json.load(f)
for i, s in enumerate(d['steps']):
    val = s.get('value', '')
    if val:
        print('Step ' + str(i+1) + ': ' + val[:300])
