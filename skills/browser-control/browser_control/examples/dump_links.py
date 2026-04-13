import sys
sys.path.insert(0, r'F:\openclaw1\.openclaw\workspace\skills\browser-control')
from browser_control.client import run_actions

r = run_actions([
    {'action': 'eval_js', 'script': "(function(){var texts=[];document.querySelectorAll('span,div,p,label').forEach(function(el){var t=el.textContent.trim();if(t&&t.length<100&&(t.includes('App ID')||t.includes('App Secret')||t.includes('appId')||t.includes('cli_')||t.includes('eyJ'))){texts.push({tag:el.tagName,t:t.substring(0,60),x:Math.round(el.getBoundingClientRect().x),y:Math.round(el.getBoundingClientRect().y)});}});return JSON.stringify(texts.slice(0,10));})();"}
], cdp_url='http://127.0.0.1:9222')
val = r['steps'][0].get('value','')
print('Cred texts:', val.encode('ascii', 'replace').decode('ascii')[:400])
