import requests, re, json, os, sys, time
sys.stdout.reconfigure(encoding='utf-8')

DATA_JS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'data.js')

with open(DATA_JS, 'r', encoding='utf-8') as f:
    c = f.read()
arr_start = c.index('[')
arr_end = c.rindex(']') + 1
data = json.loads(c[arr_start:arr_end])
prefix = c[:arr_start]
suffix = c[arr_end:]

# Read ahwak results for elcinema poster mapping
ahwak_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'results_ahwak_moslslat_ramdan_2022.json')
with open(ahwak_file, 'r', encoding='utf-8') as f:
    ahwak_data = json.load(f)

# Build title -> elcinema poster map
poster_map = {}
for s in ahwak_data:
    p = s.get('poster', '')
    if 'elcinema' in p:
        poster_map[s['title'].strip()] = p

print('Elcinema posters available: %d' % len(poster_map))

# Update data.js
updated = 0
for item in data:
    title = item.get('title', '').strip()
    if title in poster_map:
        old = item.get('poster', '')
        if 'elcinema' not in old.lower() or '_810x1080' in old:
            item['poster'] = poster_map[title]
            updated += 1

print('Updated in data.js: %d' % updated)

json_str = json.dumps(data, ensure_ascii=False)
with open(DATA_JS, 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('Saved.')
