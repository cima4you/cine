import os, re, json

def ar(t):
    return re.sub(r'[^\u0600-\u06FF\s]','',t).strip()

for fname in ['data-turkish-completed.js', 'data-turkish-ongoing.js']:
    fpath = os.path.join('data', fname)
    content = open(fpath, 'r', encoding='utf-8').read()
    m = re.search(r'=\s*(\[.*\])\s*$', content, re.DOTALL)
    data = json.loads(m.group(1))
    for d in data:
        t = d.get('title', '')
        if 'اسطنبول' in t or 'أخي' in t or 'Test' in t or 'Thank' in t:
            eps = d.get('seasons', [{}])[0].get('episodes', [])
            ep_nums = sorted([e.get('episodeNumber') or e.get('number', 0) for e in eps])
            print(f'[{fname}] {t}: {len(eps)} eps, nums={ep_nums[:10]}')
