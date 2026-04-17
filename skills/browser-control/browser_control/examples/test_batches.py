import json, sys, time
sys.path.insert(0, r'F:\openclaw1\.openclaw\workspace\skills\browser-control')
sys.stdout.reconfigure(encoding='utf-8')
from browser_control.client import run_actions

def test_batch(batch_num):
    batch_file = rf'F:\openclaw1\.openclaw\workspace\skills\browser-control\output\scope_batch_{batch_num}.json'
    try:
        with open(batch_file, 'r', encoding='utf-8') as f:
            batch_json = f.read().strip()
    except FileNotFoundError:
        return False, f'Batch {batch_num} not found'

    print(f'Batch {batch_num}: {len(batch_json)} chars: {batch_json[:80]}...')

    steps = [
        {'action': 'eval_js', 'script': "(function(){var allBtns=document.querySelectorAll('button');for(var i=0;i<allBtns.length;i++){var t=allBtns[i].textContent.trim();if(t.indexOf('Batch')>=0){allBtns[i].click();return 'OPENED';}}return 'NOT_FOUND';})();"},
        {'action': 'wait_timeout', 'ms': 3000},
        {'action': 'eval_js', 'script': "(function(){var ta=document.querySelector('textarea.inputarea');if(!ta)return 'NO_TA';ta.focus();return 'TA_OK';})();"},
        {'action': 'wait_timeout', 'ms': 1000},
        {'action': 'eval_js', 'script': f"(function(){{var ta=document.querySelector('textarea.inputarea');if(!ta)return 'NO_TA';var json='{batch_json}';var ns=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;ns.call(ta,json);ta.dispatchEvent(new Event('input',{{bubbles:true}}));return 'SET:'+ta.value.length;}}());"},
        {'action': 'wait_timeout', 'ms': 2000},
    ]

    r = run_actions(steps, cdp_url='http://127.0.0.1:9222')
    for i, s in enumerate(r['steps']):
        print(f'  Step {i+1}: {s.get("value","")[:50]}')
    return True, 'OK'

for i in range(1, 4):
    ok, msg = test_batch(i)
    print(msg)
    if not ok:
        break
    time.sleep(2)
