import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])

types = {}
for item in data:
    p = item.get('poster', '')
    if 'egydead.live' in p:
        t = item.get('type', '')
        types[t] = types.get(t, 0) + 1

print('Types of items with egydead.live posters:')
for t, cnt in sorted(types.items(), key=lambda x: -x[1]):
    print('  %s: %d' % (t, cnt))
