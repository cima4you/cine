import json
m = json.load(open('screpte/cimafre/data/cimafre_movies.json','r',encoding='utf-8'))
from collections import Counter
for cat in ['turkish-series']:
    cat_m = [x for x in m if x['cat'] == cat]
    pages = Counter(x['page'] for x in cat_m)
    print(f'{cat}: {len(cat_m)} entries, pages: {min(pages)}-{max(pages)}')
    if len(pages) > 5:
        print(f'  first 5 pages: {sorted(pages)[:5]}')
        print(f'  last 5 pages: {sorted(pages)[-5:]}')
