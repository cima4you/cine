import requests, re
from urllib.parse import urljoin

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
}

s = requests.Session()
# First visit homepage to get cookies
r = s.get('https://cimafre.site/', headers=headers, timeout=20)
print(f'Homepage: {r.status_code}, cookies: {dict(s.cookies)}')

# Now visit a watch page
r = s.get('https://cimafre.site/watch.php?vid=19997b01f', headers=headers, timeout=20)
r.encoding = 'utf-8'
print(f'Watch page: {r.status_code}, {len(r.text)} bytes')

# Check for WatchList
if 'WatchList' in r.text:
    wl = re.search(r'<ul[^>]*class="[^"]*WatchList[^"]*"[^>]*>.*?</ul>', r.text, re.DOTALL)
    if wl:
        print('WatchList UL found!')
        print(wl.group(0)[:2000])
    else:
        print('"WatchList" text found but not as UL')
else:
    print('"WatchList" NOT found in HTML')

# Check for embed_url data
for kw in ['data-embed-url', 'data-embed-id', 'data-download-url', 'li server', 'watch_url', 'server_url']:
    if kw in r.text:
        idx = r.text.index(kw)
        print(f'Found "{kw}" at pos {idx}: ...{r.text[max(0,idx-50):idx+200]}...')
