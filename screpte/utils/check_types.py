import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])

types = {}
content_types = {}
for x in data:
    t = x.get('type', '').strip()
    ct = x.get('contentType', '').strip()
    types[t] = types.get(t, 0) + 1
    content_types[ct] = content_types.get(ct, 0) + 1

print('--- types ---')
for t, n in sorted(types.items(), key=lambda x: -x[1]):
    print(f'  "{t}": {n}')

print('\n--- contentTypes ---')
for t, n in sorted(content_types.items(), key=lambda x: -x[1]):
    print(f'  "{t}": {n}')
