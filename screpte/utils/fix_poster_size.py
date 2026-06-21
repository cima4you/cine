import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = 'data.js'
RESULTS_FILE = 'scripts/larozza/data/results_larozza_ramadan_2026.json'

# Fix results file
with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
    results = json.load(f)

for s in results:
    poster = s.get('poster', '')
    if '_810x1080' in poster:
        s['poster'] = poster.replace('_810x1080', '_315x420')

with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f'Fixed {RESULTS_FILE}')

# Fix data.js
with open(DATA_DIR, 'r', encoding='utf-8') as f:
    content = f.read()
arr_start = content.index('[')
arr_end = content.rindex(']') + 1
data = json.loads(content[arr_start:arr_end])
prefix = content[:arr_start]
suffix = content[arr_end:]

fixed = 0
for item in data:
    poster = item.get('poster', '')
    if '_810x1080' in poster:
        item['poster'] = poster.replace('_810x1080', '_315x420')
        fixed += 1

print(f'Fixed {fixed} posters in data.js ({len(data)} total)')

json_str = json.dumps(data, ensure_ascii=False)
with open(DATA_DIR, 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('Done.')
