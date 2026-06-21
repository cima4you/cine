import os, re, json

for fname in ['data-turkish-completed.js']:
    fpath = os.path.join('data', fname)
    content = open(fpath, 'r', encoding='utf-8').read()
    m = re.search(r'=\s*(\[.*\])\s*$', content, re.DOTALL)
    data = json.loads(m.group(1))
    for d in data:
        t = d.get('title', '')
        if 'اسطنبول' in t or 'أخي' in t:
            eps = d.get('seasons', [{}])[0].get('episodes', [])
            ep_nums = [e.get('episodeNumber') or e.get('number', 0) for e in eps]
            print(f'{t}: {len(eps)} eps, numbers={sorted(ep_nums)[:10]}')
