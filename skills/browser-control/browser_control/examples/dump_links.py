import sys, json
sys.path.insert(0, r'F:\openclaw1\.openclaw\workspace\skills\browser-control')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
with open(r'F:\openclaw1\.openclaw\workspace\skills\browser-control\output\workflow_result.json', encoding='utf-8', errors='replace') as f:
    d = json.load(f)
print('Step1:', d['steps'][0].get('value',''))
print('Step3:', d['steps'][2].get('value',''))
