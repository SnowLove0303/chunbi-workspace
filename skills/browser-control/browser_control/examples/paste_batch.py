import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\chenz\Documents\Obsidian Vault\开发项目ing\飞书\json.md', encoding='utf-8') as f:
    content = f.read()

data = json.loads(content)
tenant = data['scopes']['tenant']
user = data['scopes']['user']
all_scopes = tenant + user

# Group into batches of ~140 chars max
batches = []
current_batch = []
current_len = 0

for scope in all_scopes:
    scope_json = f'"{scope}"'
    if current_len + len(scope_json) + 2 > 130:
        if current_batch:
            batches.append(current_batch)
        current_batch = [scope]
        current_len = len(scope_json) + 2
    else:
        current_batch.append(scope)
        current_len += len(scope_json) + 1

if current_batch:
    batches.append(current_batch)

print(f'Total scopes: {len(all_scopes)}, Batches: {len(batches)}')

for i, batch in enumerate(batches):
    # Build compact JSON for this batch
    batch_data = {"scopes": {"tenant": [s for s in batch if s in tenant], 
                          "user": [s for s in batch if s in user]}}
    batch_json = json.dumps(batch_data, separators=(',', ':'))
    print(f'Batch {i+1}: {len(batch)} scopes, {len(batch_json)} chars: {batch}')
    
    fname = rf'F:\openclaw1\.openclaw\workspace\skills\browser-control\output\scope_batch_{i+1}.json'
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(batch_json)

print('Done')
