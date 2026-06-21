#!/usr/bin/env python3
"""Add isComplete field to existing scraped data based on episode title detection."""
import sys, os, json

if len(sys.argv) < 2:
    print('Usage: python add_iscomplete.py <data.json>')
    sys.exit(1)

path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

completed = 0
for item in data:
    ct = item.get('contentType', '')
    if ct == 'series':
        eps = item.get('seasons', [{}])[0].get('episodes', [])
        has_final = any('الاخيرة' in e.get('title','') or 'الأخيرة' in e.get('title','') for e in eps)
        has_final_title = any(w in item.get('title','') for w in ['الاخيرة','والاخيرة','الأخيرة','والأخيرة','كاملة','كامله'])
        item['isComplete'] = has_final or has_final_title
        if item['isComplete']:
            completed += 1
    else:
        item['isComplete'] = False

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'Updated {len(data)} items ({completed} completed, {len(data)-completed} ongoing)')
