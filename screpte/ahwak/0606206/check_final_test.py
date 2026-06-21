import json
d = json.load(open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\data\turkish_series_detail.json', 'r', encoding='utf-8'))
out = [f'Total: {len(d)} series']
total_eps = 0
for s in d:
    eps = len(s.get('episodes', []))
    total_eps += eps
    seasons = len(s.get('seasons', []))
    out.append(f'  {repr(s.get("title","")[:50]):55s} -> {eps:4d} eps, {seasons} season(s)')
out.append(f'Total episodes: {total_eps}')
with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\data\test_result2.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('Written to test_result2.txt')
