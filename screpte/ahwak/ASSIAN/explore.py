#!/usr/bin/env python3
import json, re, os

base = 'D:\\web-secriping\\Ancien PC\\DT\\site-rachid'

# Verify Turkish merge results
print('=== TURKISH MERGE VERIFICATION ===')
for tf in ['data/data-turkish-completed.js', 'data/data-turkish-ongoing.js']:
    fp = os.path.join(base, tf)
    if os.path.exists(fp):
        c = open(fp, 'r', encoding='utf-8').read()
        m = re.search(r'const (\w+) = (\[.*?\])\s*;?\s*$', c, re.DOTALL)
        if m:
            items = json.loads(m.group(2))
            total_eps = sum(sum(len(s.get('episodes',[])) for s in x.get('seasons',[])) for x in items)
            total_sv = sum(sum(len(e.get('servers',[])) for s in x.get('seasons',[]) for e in s.get('episodes',[])) for x in items)
            dirty = sum(1 for x in items if x.get('title','').startswith('مسلسل') or 'مترجم' in x.get('title',''))
            print(f'{tf}: {len(items)} items, {total_eps} eps, {total_sv} servers, dirty={dirty}')
            print(f'  First: {items[0]["title"][:50]}')
            if dirty:
                bad = [x for x in items if x.get('title','').startswith('مسلسل') or 'مترجم' in x.get('title','')]
                for x in bad:
                    print(f'  DIRTY: {x["title"][:60]}')
        else:
            print(f'{tf}: ERROR - no array found')
