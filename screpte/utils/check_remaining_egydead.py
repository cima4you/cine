import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])

remaining = [(i, x) for i, x in enumerate(data) if 'egydead.live' in x.get('poster', '')]
print('Remaining with egydead.live posters: %d' % len(remaining))
for i, item in remaining:
    print('  [%d] %s | type=%s | year=%s' % (i, item.get('title','')[:40], item.get('type',''), item.get('year','')))
