import os, hashlib

files = {
    'requests': 'screpte/cimafre/data/detail.html',
    'cloudscraper': 'screpte/cimafre/data/cloudflare_detail.html',
    'selenium': 'screpte/cimafre/data/selenium_detail.html',
}

for name, path in files.items():
    if os.path.exists(path):
        t = open(path, 'r', encoding='utf-8').read()
        h = hashlib.md5(t.encode('utf-8')).hexdigest()
        print(f'{name}: {len(t)}b, md5={h}')
        print(f'  WatchList count: {t.count("WatchList")}')
        print(f'  data-embed-url in non-script: {len([l for l in t.split(chr(10)) if "data-embed-url" in l and "script" not in l[:20]])}')
        # Check for any ul with class WatchList
        import re
        m = re.search(r'<ul[^>]*WatchList', t)
        print(f'  UL.WatchList exists: {m is not None}')
        if m:
            idx = max(0, m.start()-100)
            print(f'  Context: ...{t[idx:m.end()+200]}...')
    else:
        print(f'{name}: NOT FOUND')
