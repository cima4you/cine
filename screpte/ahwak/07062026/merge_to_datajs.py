#!/usr/bin/env python3
"""
Merge scraped data from a JSON file into data.js.
Preserves existing items, only adds new ones (dedup by title).
"""
import sys, os, json, re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # rachid-site/
DATA_JS = os.path.join(BASE_DIR, 'data.js')

def resolve_datajs(path):
    if os.path.exists(path):
        return path
    # try relative to script dir, then CWD
    for base in [BASE_DIR, os.getcwd()]:
        p = os.path.join(base, 'data.js')
        if os.path.exists(p):
            return p
    return path

def normalize(t):
    import re
    t = re.sub(r'[\u064B-\u0652]', '', t)
    t = re.sub(r'\s+', '', t)
    return t.strip().lower()

def main():
    if len(sys.argv) < 2:
        print(f'Usage: python {os.path.basename(__file__)} <new_data.json> [data.js path]')
        sys.exit(1)

    new_path = sys.argv[1]
    data_js_path = resolve_datajs(sys.argv[2] if len(sys.argv) > 2 else DATA_JS)

    if not os.path.exists(data_js_path):
        print(f'ERROR: {data_js_path} not found')
        sys.exit(1)

    # Read new data
    with open(new_path, 'r', encoding='utf-8') as f:
        new_items = json.load(f)
    print(f'New data: {len(new_items)} items')

    # Read data.js
    with open(data_js_path, 'r', encoding='utf-8') as f:
        js_text = f.read()

    # Locate the JSON array
    start = js_text.index('[')
    end = js_text.rindex(']') + 1
    prefix = js_text[:start]
    suffix = js_text[end:]

    existing = json.loads(js_text[start:end])
    print(f'Existing data.js: {len(existing)} items')

    # Build dedup set from existing
    existing_keys = {normalize(item.get('title', '')) for item in existing}

    # Filter new items
    added = []
    skipped = 0
    for item in new_items:
        key = normalize(item.get('title', ''))
        if key and key in existing_keys:
            skipped += 1
        else:
            existing.append(item)
            added.append(item['title'][:60])

    # Write back
    merged_json = json.dumps(existing, ensure_ascii=False)
    with open(data_js_path, 'w', encoding='utf-8') as f:
        f.write(prefix + merged_json + suffix)

    print(f'Added: {len(added)}, Skipped (duplicate): {skipped}')
    print(f'Total now: {len(existing)} items')
    if added:
        print('New titles:')
        for t in added:
            print(f'  • {t}')

if __name__ == '__main__':
    main()
