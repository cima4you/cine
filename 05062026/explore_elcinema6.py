import requests, re, sys, urllib3
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
})
s.verify = False
s.get('https://www.elcinema.com/', timeout=15)

# Try longer queries
tests = [
    'مسلسلات 2025',
    '2025 مسلسلات رمضان',
    'arabic series 2025',
    'TV series 2025',
    'مسلسل 2025 رمضان',
]
for q in tests:
    r = s.get('https://www.elcinema.com/search/', params={'q': q}, timeout=15)
    links = re.findall(r'href="(/work/\d+/)"', r.text) if r.status_code == 200 else []
    print(f'q="{q}": HTTP {r.status_code}, links={len(links)}')

# Try to understand what the minimum search query is
print('\n=== Test query length ===')
for length in range(3, 10):
    q = 'مس' + 'ل' * (length - 2)  # مسل, مسلل, etc
    r = s.get('https://www.elcinema.com/search/', params={'q': q}, timeout=15)
    ok = r.status_code == 200
    links = len(re.findall(r'href="(/work/\d+/)"', r.text)) if ok else 0
    if ok:
        print(f'q="{q}" ({len(q)} chars): HTTP 200, links={links}')

# Check if elcinema has a browse page with different URL
print('\n=== Alternative browse URLs ===')
for url in [
    'https://www.elcinema.com/browse/1/',
    'https://www.elcinema.com/browse/ar/series/',
    'https://www.elcinema.com/ar/browse/series/',
    'https://www.elcinema.com/en/browse/series/',
    'https://www.elcinema.com/browse/series-2025/',
    'https://www.elcinema.com/explore/',
]:
    try:
        r = s.get(url, timeout=15)
        print(f'{url}: HTTP {r.status_code}, len={len(r.text)}')
    except:
        print(f'{url}: ERROR')

# Check if there's a year-based category
print('\n=== Category/year URLs ===')
for year in [2025, 2024]:
    for url in [
        f'https://www.elcinema.com/year/{year}/',
        f'https://www.elcinema.com/calendar/{year}/',
        f'https://www.elcinema.com/browse/series/?year={year}',
    ]:
        try:
            r = s.get(url, timeout=15)
            links = len(re.findall(r'href="(/work/\d+/)"', r.text)) if r.status_code == 200 else 0
            print(f'{url}: HTTP {r.status_code}, links={links}')
        except:
            print(f'{url}: ERROR')
