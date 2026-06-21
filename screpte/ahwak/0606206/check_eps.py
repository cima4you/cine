import json
d = json.load(open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\data\turkish_series_detail.json', 'r', encoding='utf-8'))
out = []
for s in d:
    if 'ورود' in s.get('title', '') or 'ورود' in s.get('title', ''):
        eps = s.get('episodes', [])
        out.append(f'Title: {repr(s["title"])}')
        out.append(f'URL: {s["url"]}')
        out.append(f'Vid: {s.get("vid","")}')
        out.append(f'Episodes ({len(eps)}):')
        for e in eps:
            out.append(f'  Ep {e.get("episodeNumber")}: {repr(e.get("title","")[:60])}')
        seasons = s.get('seasons', [])
        out.append(f'Seasons ({len(seasons)}):')
        for sn in seasons:
            out.append(f'  S{sn.get("seasonNumber")}: {repr(sn.get("name",""))}')
        with open(r'D:\web-secriping\Ancien PC\DT\site-rachid\screpte\ahwak\0606206\data\check_ورود.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(out))
        break
