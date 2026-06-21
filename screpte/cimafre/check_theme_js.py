import requests, re

headers = {'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'ar,en'}

files = [
    'https://cimafre.site/templates/echo/js/theme1.js?v=0.1',
    'https://cimafre.site/templates/echo/js/jquery.plugins.a.js',
    'https://cimafre.site/templates/echo/js/jquery.plugins.b.js',
    'https://cimafre.site/templates/echo/js/lightbox.dev.js',
]

for url in files:
    r = requests.get(url, headers=headers, timeout=20)
    r.encoding = 'utf-8'
    t = r.text
    name = url.split('/')[-1].split('?')[0]
    print(f'=== {name} ({len(t)} bytes) ===')
    # Look for WatchList, server, source, embed, AJAX
    for kw in ['WatchList', 'server', 'source', 'embed', 'data-embed', 'load_stream', 'download_url', 'ajax']:
        lines = [l.strip() for l in t.split('\n') if kw.lower() in l.lower() and len(l.strip()) > 5]
        if lines:
            print(f'  {kw}: {len(lines)} lines')
            for l in lines[:3]:
                print(f'    {l[:200]}')
    print()
