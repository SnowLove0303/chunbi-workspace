import sys
sys.path.insert(0, r'F:\openclaw1\.openclaw\workspace\skills\browser-control')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from browser_control.client import run_actions

# Navigate to event page
r = run_actions([
    {'action': 'eval_js', 'script': "window.location.href='https://open.feishu.cn/app/cli_a95620cbb8399cdd/event';return 'NAVIGATING';"},
    {'action': 'wait_timeout', 'ms': 5000},
    {'action': 'eval_js', 'script': "(function(){var allEls=document.querySelectorAll('*');var result=[];allEls.forEach(function(e){var t=e.textContent||'';if(t.indexOf('im.message')>=0){var r=e.getBoundingClientRect();result.push({t:t.substring(0,40),x:Math.round(r.x),y:Math.round(r.y)});}});return JSON.stringify(result.slice(0,5));})();"}
], cdp_url='http://127.0.0.1:9222')

print('Step1:', r['steps'][0].get('value',''))
print('Step3:', r['steps'][2].get('value','')[:500])