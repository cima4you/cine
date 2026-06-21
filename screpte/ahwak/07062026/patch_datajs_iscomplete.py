#!/usr/bin/env python3
"""Add/update isComplete field on Asian series already in data.js."""
import sys, os, json, re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))

def resolve_datajs():
    for base in [BASE_DIR, os.getcwd()]:
        p = os.path.join(base, 'data.js')
        if os.path.exists(p):
            return p
    return os.path.join(BASE_DIR, 'data.js')

def main():
    data_js = resolve_datajs()
    if not os.path.exists(data_js):
        print(f'ERROR: data.js not found')
        sys.exit(1)

    with open(data_js, 'r', encoding='utf-8') as f:
        js_text = f.read()

    start = js_text.index('[')
    end = js_text.rindex(']') + 1
    prefix = js_text[:start]
    suffix = js_text[end:]

    data = json.loads(js_text[start:end])
    updated = 0
    for item in data:
        ct = item.get('contentType', '')
        if ct == 'series':
            seasons = item.get('seasons', [])
            eps = seasons[0].get('episodes', []) if seasons else []
            title = item.get('title', '')
            has_final_ep = any('الاخيرة' in e.get('title','') or 'الأخيرة' in e.get('title','') for e in eps)
            has_final_title = any(w in title for w in ['الاخيرة','والاخيرة','الأخيرة','والأخيرة','كاملة','كامله'])
            ic = has_final_ep or has_final_title
            if item.get('isComplete') != ic:
                item['isComplete'] = ic
                updated += 1

    # Also check movies: set isComplete = false for all movies
    for item in data:
        if item.get('contentType') == 'movie' and 'isComplete' not in item:
            item['isComplete'] = False
            updated += 1

    merged_json = json.dumps(data, ensure_ascii=False)
    with open(data_js, 'w', encoding='utf-8') as f:
        f.write(prefix + merged_json + suffix)

    print(f'Updated {updated} items with isComplete')
    print(f'Total: {len(data)} items in data.js')

if __name__ == '__main__':
    main()
