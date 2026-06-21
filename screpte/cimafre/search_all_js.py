import requests, re

headers = {'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'ar,en'}
s = requests.Session()

files = [
    'https://cimafre.site/templates/echo/js/theme1.js?v=0.1',
    'https://cimafre.site/templates/echo/js/jquery.plugins.a.js',
    'https://cimafre.site/templates/echo/js/jquery.plugins.b.js',
    'https://cimafre.site/templates/echo/js/lightbox.dev.js',
    'https://cimafre.site/templates/echo/js/jasny-bootstrap.min.js',
    'https://cimafre.site/templates/echo/js/jquery.readmore.js',
]

all_js = ''
for url in files:
    r = s.get(url, headers=headers, timeout=20)
    r.encoding = 'utf-8'
    t = r.text
    name = url.split('/')[-1].split('?')[0]
    all_js += f'\n// === {name} ===\n' + t

# Search for anything that builds HTML or sets data attributes
for kw in ['WatchList', 'data-embed', 'DownloadList', 'download_url', 'server', '.html(', 'append', 'prepend', 'write']:
    lines = [l.strip() for l in all_js.split('\n') if kw.lower() in l.lower() and len(l.strip()) > 3]
    if lines:
        print(f'=== {kw} ({len(lines)} lines) ===')
        for l in lines[:5]:
            print(f'  {l[:250]}')
