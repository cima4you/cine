import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = 'data.js'
RESULTS_FILE = 'scripts/larozza/data/results_larozza_ramadan_2026.json'

with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
    new_data = json.load(f)

# Build poster map
poster_map = {}
for s in new_data:
    title = s['title'].strip()
    poster = s.get('poster', '')
    if 'elcinema' in poster.lower():
        poster_map[title] = poster

print(f'New elcinema posters: {len(poster_map)}')

# Load data.js
with open(DATA_DIR, 'r', encoding='utf-8') as f:
    content = f.read()
arr_start = content.index('[')
arr_end = content.rindex(']') + 1
data = json.loads(content[arr_start:arr_end])
prefix = content[:arr_start]
suffix = content[arr_end:]

# Update posters
updated = 0
for item in data:
    title = item.get('title', '').strip()
    if title in poster_map:
        old = item.get('poster', '')
        new = poster_map[title]
        if old != new:
            item['poster'] = new
            updated += 1

print(f'Updated {updated} posters in data.js ({len(data)} total)')

# Write back
json_str = json.dumps(data, ensure_ascii=False)
with open(DATA_DIR, 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('Done.')
