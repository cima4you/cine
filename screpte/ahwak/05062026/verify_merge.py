import json, re
content = open('data.js', 'r', encoding='utf-8').read()
json_str = content.split('const contentData = ')[1].rsplit(';', 1)[0]
data = json.loads(json_str)
ts = [s for s in data if s.get('type') in ('تركي','تركيي') and s.get('contentType') == 'series']
tm = [s for s in data if s.get('type') in ('تركي','تركيي') and s.get('contentType') == 'movie']
tot_eps = sum(len(s.get('seasons',[{}])[0].get('episodes',[])) for s in ts if s.get('seasons'))
print(f'Total: {len(data)}, Turkish series: {len(ts)}, Turkish movies: {len(tm)}, Episodes: {tot_eps}\n')
for s in ts:
    eps = len(s.get('seasons',[{}])[0].get('episodes',[])) if s.get('seasons') else 0
    print(f'  {s["title"][:55].ljust(55)} {eps} eps')
