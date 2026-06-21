import json, os, re

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_JS_PATH = os.path.join(SCRIPT_DIR, 'data.js')
SERIES_FILE = os.path.join(SCRIPT_DIR, 'data_egydead_series.json')

def load_data_js():
    with open(DATA_JS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    arr_start = content.index('[')
    arr_end = content.rindex(']') + 1
    data = json.loads(content[arr_start:arr_end])
    return data, content[:arr_start], content[arr_end:]

def save_data_js(data, prefix, suffix):
    json_str = json.dumps(data, ensure_ascii=False)
    with open(DATA_JS_PATH, 'w', encoding='utf-8') as f:
        f.write(prefix + json_str + suffix)

with open(SERIES_FILE, 'r', encoding='utf-8') as f:
    egydead_data = json.load(f)

egydead_titles = set()
for item in egydead_data:
    title = item.get('title', '').strip()
    if title:
        egydead_titles.add(title.lower())

data, prefix, suffix = load_data_js()
before = len(data)

filtered = []
removed = 0
for item in data:
    title = item.get('title', '').strip().lower()
    if title in egydead_titles:
        removed += 1
    else:
        filtered.append(item)

save_data_js(filtered, prefix, suffix)

print(f'Removed {removed} items added by merge_egydead_series.py')
print(f'Before: {before}, Now: {len(filtered)}')
