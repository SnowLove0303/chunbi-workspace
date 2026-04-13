import json
with open(r'F:\openclaw1\.openclaw\workspace\skills\browser-control\output\workflow_result.json', encoding='utf-8', errors='replace') as f:
    d = json.load(f)
print('Steps:')
for i, s in enumerate(d['steps']):
    ok = s.get('ok')
    val = s.get('value', '')
    err = s.get('error', '')
    if not ok:
        print('  Step ' + str(i+1) + ': FAIL - ' + err[:100])
    elif val:
        print('  Step ' + str(i+1) + ': ' + s['action'] + ' -> ' + val[:80])
    else:
        print('  Step ' + str(i+1) + ': ' + s['action'] + ' -> OK')
