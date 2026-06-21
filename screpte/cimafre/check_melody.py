import requests, re

urls = [
    'https://cimafre.site/js/melody.dev.js',
    'https://cimafre.site/templates/echo/js/melody.dev.js',
]
for url in urls:
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
    r.encoding = 'utf-8'
    t = r.text
    name = url.split('/')[-1]
    print(f'{name}: {len(t)} bytes')
    for kw in ['ajax', 'embed', 'sourc', 'WatchList', 'load_stream', 'switch_source', 'get_video']:
        lines = [l.strip() for l in t.split('\n') if kw.lower() in l.lower() and len(l.strip()) > 5]
        if lines:
            print(f'  {kw}: {len(lines)} lines')
            for l in lines[:3]:
                print(f'    {l[:150]}')
    print()
