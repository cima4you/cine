import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])
prefix = c[:c.index('[')]
suffix = c[c.rindex(']')+1:]

remaining = [(i, x) for i, x in enumerate(data) if 'egydead.live' in x.get('poster', '')]
print('Setting empty poster for %d items (will use HTML fallback)...' % len(remaining))

for idx, item in remaining:
    print('  [%d] %s' % (idx, item['title'][:40]))
    data[idx]['poster'] = ''

json_str = json.dumps(data, ensure_ascii=False)
with open('data.js', 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('Done. %d items will use fallback placeholder.' % len(remaining))
