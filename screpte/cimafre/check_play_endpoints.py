import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
    'Referer': 'https://cimafre.site/',
}

s = requests.Session()
s.get('https://cimafre.site/', headers=headers, timeout=20)

vid = '19997b01f'

endpoints = [
    f'https://cimafre.site/play.php?vid={vid}',
    f'https://cimafre.site/sources.php?vid={vid}',
    f'https://cimafre.site/video.php?vid={vid}',
    f'https://cimafre.site/get_source.php?vid={vid}',
    f'https://cimafre.site/api.php?vid={vid}',
    f'https://cimafre.site/api/video/{vid}',
    f'https://cimafre.site/json.php?vid={vid}',
    f'https://cimafre.site/data.php?vid={vid}',
]

for ep in endpoints:
    try:
        r = s.get(ep, headers=headers, timeout=15)
        r.encoding = 'utf-8'
        print(f'{ep.split(".site")[1]}: {r.status_code}, {len(r.text)}b')
        if len(r.text) > 10:
            print(f'  {r.text[:300]}')
    except Exception as e:
        print(f'{ep.split(".site")[1]}: ERROR {e}')
