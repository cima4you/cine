import requests, re

domains = ['cimafre.site', 'cimafre.beauty', 'cimafree.beauty']
vid = '19997b01f'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
}

for domain in domains:
    try:
        s = requests.Session()
        s.get(f'https://{domain}/', headers=headers, timeout=15)
        r = s.get(f'https://{domain}/watch.php?vid={vid}', headers=headers, timeout=15)
        r.encoding = 'utf-8'
        has_wl = 'WatchList' in r.text
        has_ul_wl = bool(re.search(r'<ul[^>]*WatchList', r.text))
        has_dl = bool(re.search(r'data-embed-url', r.text))
        print(f'{domain}: {r.status_code}, {len(r.text)}b, WatchList={has_wl}, UL={has_ul_wl}, data-embed-url={has_dl}')
        if has_ul_wl:
            m = re.search(r'<ul[^>]*class="[^"]*WatchList[^"]*"[^>]*>.*?</ul>', r.text, re.DOTALL)
            if m:
                print(f'  {m.group(0)[:500]}')
    except Exception as e:
        print(f'{domain}: ERROR {e}')
