import requests, re

# Try to find the AJAX endpoint by looking at common Melody CMS patterns
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
    'Referer': 'https://cimafre.site/',
    'X-Requested-With': 'XMLHttpRequest',
}

vid = '19997b01f'

# Common Melody CMS AJAX endpoints
endpoints = [
    f'https://cimafre.site/ajax.php?vid={vid}&do=get-servers',
    f'https://cimafre.site/ajax.php?vid={vid}&do=video-sources',
    f'https://cimafre.site/ajax.php?do=get_sources&vid={vid}',
    f'https://cimafre.site/ajax/get_sources.php?vid={vid}',
    f'https://cimafre.site/ajax/get_servers.php?vid={vid}',
    f'https://cimafre.site/ajax.php?action=get_sources&vid={vid}',
    f'https://cimafre.site/ajax.php?action=get_servers&vid={vid}',
    f'https://cimafre.site/includes/ajax.php?do=get_sources&vid={vid}',
    f'https://cimafre.site/ajax/sources.php?vid={vid}',
    f'https://cimafre.site/ajax/servers.php?vid={vid}',
    f'https://cimafre.site/ajax.php?vid={vid}',
]

for ep in endpoints:
    try:
        r = requests.get(ep, headers=headers, timeout=15)
        print(f'{ep.split("cimafre.site")[1]} -> {r.status_code} ({len(r.text)} bytes): {r.text[:300]}')
    except Exception as e:
        print(f'{ep.split("cimafre.site")[1]} -> ERROR: {e}')
