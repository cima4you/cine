import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])

egydead = []
for i, item in enumerate(data):
    poster = item.get('poster', '')
    if 'egydead.live' in poster:
        egydead.append((i, item.get('title','')[:40], poster[:80]))

print('Total egydead.live poster URLs: %d' % len(egydead))
for idx, title, poster in egydead[:10]:
    print('  [%d] %s' % (idx, title))
    print('       %s' % poster)
