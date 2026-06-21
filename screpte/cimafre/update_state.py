import json
s = json.load(open('screpte/cimafre/data/cimafre_state.json','r',encoding='utf-8'))
s['scraped_cats'] = list(set(s['scraped_cats']) | {'turkish-series'})
s['cat_pages'] = {}
json.dump(s, open('screpte/cimafre/data/cimafre_state.json','w',encoding='utf-8'), ensure_ascii=False)
print(f'State: {s}')
