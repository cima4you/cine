import json, os, re

DATA_JS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data.js')

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

data, prefix, suffix = load_data_js()
before = len(data)

filtered = [item for item in data if 'egydead' not in str(item).lower() and 'tv8.egydead' not in str(item).lower()]
removed = before - len(filtered)

save_data_js(filtered, prefix, suffix)

print(f'Removed {removed} EgyDead items')
print(f'Before: {before}, Now: {len(filtered)}')
