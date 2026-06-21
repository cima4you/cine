import json
d = json.load(open('data/turkish_series_detail.json','r',encoding='utf-8'))
for s in d:
    title = s['title'][:40]
    seasons = [ss['seasonNumber'] for ss in s.get('seasons',[])]
    eps = len(s.get('episodes',[]))
    print(f'{title:40s} | seasons={seasons} | eps={eps:3d}')
