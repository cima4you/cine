#!/usr/bin/env python3
import json, re, os, sys
sys.stdout = open(sys.stdout.fileno(), 'w', encoding='utf-8', buffering=1)

for path, label in [
    ('data/data-asian-series-completed.js', 'completed'),
    ('data/data-asian-series-ongoing.js', 'ongoing'),
]:
    c = open(path, 'r', encoding='utf-8').read()
    m = re.search(r'const (\w+) = (\[.*?\])\s*;?\s*$', c, re.DOTALL)
    items = json.loads(m.group(2))
    total_eps = sum(
        sum(len(e.get('episodes', [])) for e in x.get('seasons', []))
        for x in items
    )
    print(f'{label}: {len(items)} items, {total_eps} eps total, var={m.group(1)}')
    print(f'  First item: {items[0]["title"][:60]}')
    for item in items[:3]:
        ic = item.get('isComplete', 'N/A')
        eps = sum(len(s.get('episodes', [])) for s in item.get('seasons', []))
        print(f'    "{item["title"][:50]}" — {eps} eps, isComplete={ic}')

# Check sample titles have no "مسلسل" prefix
for path in ['data/data-asian-series-completed.js', 'data/data-asian-series-ongoing.js']:
    c = open(path, 'r', encoding='utf-8').read()
    m = re.search(r'\[.*\]', c, re.DOTALL)
    items = json.loads(m.group())
    bad = [x for x in items if isinstance(x, dict) and x.get('title', '').startswith('مسلسل')]
    if bad:
        print(f'\n⚠ In {os.path.basename(path)} — {len(bad)} titles with مسلسل prefix:')
        for x in bad:
            eps = sum(len(s.get('episodes', [])) for s in x.get('seasons', []))
            print(f'  "{x["title"][:60]}" — {eps} eps, isComplete={x.get("isComplete")}')
    else:
        print(f'\n✅ {os.path.basename(path)} — all titles clean')
