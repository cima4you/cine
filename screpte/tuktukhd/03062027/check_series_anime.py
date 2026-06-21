import json, re, requests, base64, concurrent.futures, html

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

# Check the 6 series without servers
indices = [712, 713, 715, 716, 717, 718]
for idx in indices:
    item = d[idx]
    print('Index {}: "{}" ({})'.format(idx, item.get('title','').strip()[:60], item.get('year','')))
    print('  Type: {}'.format(item.get('type','')))
    print('  Has seasons: {}'.format('seasons' in item))
    if 'seasons' in item:
        s = item['seasons']
        if isinstance(s, list):
            print('  Seasons count: {}'.format(len(s)))
            if s:
                print('  Season 0 keys: {}'.format(list(s[0].keys())[:5]))
                if 'episodes' in s[0]:
                    eps = s[0]['episodes']
                    if isinstance(eps, list) and eps:
                        print('  Episodes count: {}'.format(len(eps)))
                        print('  Episode 0 keys: {}'.format(list(eps[0].keys())[:5]))
                        for k in ['servers', 'downloadServers']:
                            if k in eps[0]:
                                v = eps[0][k]
                                if isinstance(v, list):
                                    print('  {}: {} items'.format(k, len(v)))
                                    for sv in v[:3]:
                                        print('    - {}: {}'.format(sv.get('name','')[:30], sv.get('url','')[:40] if sv.get('url') else sv.get('real_url','')[:40] if sv.get('real_url') else 'N/A'))
    print()
