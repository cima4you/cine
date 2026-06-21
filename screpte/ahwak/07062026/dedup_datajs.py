#!/usr/bin/env python3
"""Remove duplicate series from data.js, keeping the one with the most episodes."""
import sys, os, json, re

def normalize(t):
    t = re.sub(r'[\u064B-\u0652]', '', t)
    t = re.sub(r'\s+', '', t)
    return t.strip().lower()

def count_eps(item):
    if item.get('contentType') == 'series':
        seasons = item.get('seasons', [])
        return sum(len(s.get('episodes', [])) for s in seasons) if seasons else 0
    return 0

def resolve_datajs():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base = os.path.dirname(os.path.dirname(script_dir))
    for d in [base, os.getcwd()]:
        p = os.path.join(d, 'data.js')
        if os.path.exists(p):
            return p
    return os.path.join(base, 'data.js')

def main():
    data_js = sys.argv[1] if len(sys.argv) > 1 else resolve_datajs()
    if not os.path.exists(data_js):
        print(f'ERROR: {data_js} not found')
        sys.exit(1)

    with open(data_js, 'r', encoding='utf-8') as f:
        js_text = f.read()

    start = js_text.index('[')
    end = js_text.rindex(']') + 1
    prefix = js_text[:start]
    suffix = js_text[end:]

    data = json.loads(js_text[start:end])

    groups = {}  # norm_key -> list of (index, item)
    for i, item in enumerate(data):
        key = normalize(item.get('title', ''))
        if not key:
            continue
        if key not in groups:
            groups[key] = []
        groups[key].append((i, item))

    removed = 0
    kept_indices = set(range(len(data)))
    for key, items in groups.items():
        if len(items) < 2:
            continue
        # find the one with most episodes
        best_idx, best_item = max(items, key=lambda x: count_eps(x[1]))
        for idx, item in items:
            if idx != best_idx:
                kept_indices.discard(idx)
                removed += 1
                eps_this = count_eps(item)
                eps_best = count_eps(best_item)
                print(f'  REMOVED ({eps_this} eps) → KEPT ({eps_best} eps): {item["title"][:60]}')

    deduped = [data[i] for i in sorted(kept_indices)]
    merged_json = json.dumps(deduped, ensure_ascii=False)
    with open(data_js, 'w', encoding='utf-8') as f:
        f.write(prefix + merged_json + suffix)

    print(f'\nRemoved {removed} duplicates')
    print(f'Before: {len(data)}, After: {len(deduped)}')

if __name__ == '__main__':
    main()
