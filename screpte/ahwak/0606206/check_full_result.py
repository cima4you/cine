import json
d = json.load(open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\data\turkish_series_detail.json', 'r', encoding='utf-8'))

out = [f'Total: {len(d)} series']
total_eps = 0
multi_season = 0
zero_eps = 0
for s in d:
    eps = len(s.get('episodes', []))
    total_eps += eps
    seasons = len(s.get('seasons', []))
    if seasons > 1:
        multi_season += 1
    if eps == 0:
        zero_eps += 1
    out.append(f'  {repr(s.get("title","")[:50]):55s} -> {eps:4d} eps, {seasons} season(s)')

out.append(f'')
out.append(f'Total episodes: {total_eps}')
out.append(f'Multi-season series: {multi_season}')
out.append(f'Zero-episode series: {zero_eps}')

with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\data\full_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('Written to full_result.txt')
