#!/usr/bin/env python3
"""
Remove larozza sources from data.js.
Usage: python remove_larozza.py
"""
import json, os, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(PROJECT_DIR, 'data.js')
RESULTS_DIR = os.path.join(PROJECT_DIR, 'scripts', 'larozza', 'data')

with open(DATA_DIR, 'r', encoding='utf-8') as f:
    content = f.read()
arr_start = content.index('[')
arr_end = content.rindex(']') + 1
data = json.loads(content[arr_start:arr_end])
prefix = content[:arr_start]
suffix = content[arr_end:]

# Get all larozza titles from results files
larozza_titles = set()
for rf in glob.glob(os.path.join(RESULTS_DIR, '*.json')):
    with open(rf, 'r', encoding='utf-8') as f:
        for item in json.load(f):
            larozza_titles.add(item['title'].strip())

before = len(data)
new_data = [item for item in data if item.get('title', '').strip() not in larozza_titles]
removed = before - len(new_data)
print(f'Before: {before}, Removed: {removed}, After: {len(new_data)}')

json_str = json.dumps(new_data, ensure_ascii=False)
with open(DATA_DIR, 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('Done.')
