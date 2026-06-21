import json
m = json.load(open('screpte/cimafre/data/cimafre_movies.json','r',encoding='utf-8'))
s = json.load(open('screpte/cimafre/data/cimafre_state.json','r',encoding='utf-8'))
from collections import Counter
cats = Counter(x['cat'] for x in m)
print(f'Total movies saved: {len(m)}')
for k,v in sorted(cats.items()):
    print(f'  {k}: {v}')
print(f'State scraped_cats: {s["scraped_cats"]}')
