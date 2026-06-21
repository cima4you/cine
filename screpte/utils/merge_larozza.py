#!/usr/bin/env python3
"""
Merge larozza results into data.js.
Usage: python merge_larozza.py
"""
import json, os, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(PROJECT_DIR, 'data.js')
RESULTS_DIR = os.path.join(PROJECT_DIR, 'scripts', 'larozza', 'data')

# Load data.js
print('جارٍ تحميل data.js...', flush=True)
with open(DATA_DIR, 'r', encoding='utf-8') as f:
    content = f.read()
arr_start = content.index('[')
arr_end = content.rindex(']') + 1
data = json.loads(content[arr_start:arr_end])
prefix = content[:arr_start]
suffix = content[arr_end:]

before = len(data)

# Find larozza results files
result_files = glob.glob(os.path.join(RESULTS_DIR, 'results_larozza_*.json'))
AHWAK_DIR = os.path.join(PROJECT_DIR, 'scripts', 'ahwak', 'data')
result_files += glob.glob(os.path.join(AHWAK_DIR, 'results_ahwak_*.json'))
result_files += glob.glob(os.path.join(AHWAK_DIR, 'results_yam_*.json'))
LAROZZA_DIR = os.path.join(PROJECT_DIR, 'scripts', 'larozza', 'data')
result_files += glob.glob(os.path.join(LAROZZA_DIR, 'results_yachts_*.json'))
print(f'Found {len(result_files)} files:')
for rf in result_files:
    print(f'  {os.path.basename(rf)}')

# Build dedup index (by title)
existing_titles = {}
for i, item in enumerate(data):
    title = item.get('title', '').strip()
    if title:
        existing_titles[title] = i

for rf in result_files:
    with open(rf, 'r', encoding='utf-8') as f:
        new_items = json.load(f)
    
    added = 0
    skipped = 0
    for item in new_items:
        title = item.get('title', '').strip()
        if not title:
            continue
        if title in existing_titles:
            skipped += 1
        else:
            data.append(item)
            existing_titles[title] = len(data) - 1
            added += 1
    
    print(f'\n--- {os.path.basename(rf)} ---')
    print(f'  Added: {added}, Skipped: {skipped}')
    print(f'  data.js: {len(data)} items')

print(f'\nTotal: +{len(data)-before} added, {before} before, {len(data)} now')

# Write back
json_str = json.dumps(data, ensure_ascii=False)
with open(DATA_DIR, 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)

# Statistics
def show_stats(new_items, label):
    total_eps = sum(len(s['seasons'][0]['episodes']) for s in new_items)
    total_srv = sum(len(e['servers']) for s in new_items for e in s['seasons'][0]['episodes'])
    series_data = [(s['title'], len(s['seasons'][0]['episodes']), sum(len(e['servers']) for e in s['seasons'][0]['episodes'])) for s in new_items]
    
    print(f'\n{"="*50}')
    print(f'إحصائيات {label}')
    print(f'{"="*50}')
    print(f'  المسلسلات: {len(new_items)}')
    print(f'  الحلقات:   {total_eps}')
    print(f'  السيرفرات: {total_srv}')
    print(f'  معدل:      {total_srv//total_eps} سيرفر/حلقة')
    print()
    print('  أكثر 5:')
    for t, e, srv in sorted(series_data, key=lambda x: -x[1])[:5]:
        print(f'    {t}: {e} حلقة, {srv} سيرفر')
    print()
    print('  أقل 5:')
    for t, e, srv in sorted(series_data, key=lambda x: x[1])[:5]:
        print(f'    {t}: {e} حلقة')

for rf in result_files:
    with open(rf, 'r', encoding='utf-8') as f:
        new_items = json.load(f)
    show_stats(new_items, os.path.basename(rf))

print(f'\nDone. ({len(data)} عنصر في data.js)')
