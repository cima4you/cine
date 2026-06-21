import requests, re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
}
s = requests.Session()
s.get('https://cimafre.site/', headers=headers, timeout=20)

vid = '19997b01f'

endpoints = [
    f'https://cimafre.site/watch.php?vid={vid}',
    f'https://cimafre.site/ajax.php?p=video&do=get-sources&vid={vid}',
    f'https://cimafre.site/ajax.php?p=video&do=servers&vid={vid}',
    f'https://cimafre.site/ajax.php?p=video&do=source&vid={vid}',
    f'https://cimafre.site/ajax.php?p=video&vid={vid}',
    f'https://cimafre.site/ajax.php?vid={vid}&do=get-sources',
    f'https://cimafre.site/ajax.php?vid={vid}&do=servers',
    f'https://cimafre.site/ajax.php?vid={vid}&p=video',
]

for ep in endpoints:
    r = s.get(ep, headers=headers, timeout=15)
    r.encoding = 'utf-8'
    name = ep.split('cimafre.site')[1]
    size = len(r.text)
    has_data = len(r.text) > 10
    print(f'{name}: {r.status_code}, {size}b, has_data={has_data}')
    if has_data:
        print(f'  {r.text[:300]}')
