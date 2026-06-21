import requests, re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'max-age=0',
    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
}

s = requests.Session()
# First visit homepage
r = s.get('https://cimafre.site/', headers=headers, timeout=20)
print(f'Homepage: {r.status_code}')

# Now fetch the watch page
r = s.get('https://cimafre.site/watch.php?vid=19997b01f', headers=headers, timeout=20)
r.encoding = 'utf-8'
t = r.text
print(f'Watch page: {r.status_code}, {len(t)} bytes')

# Check for WatchList
m = re.search(r'<ul[^>]*class="[^"]*WatchList[^"]*"[^>]*>.*?</ul>', t, re.DOTALL)
if m:
    print('WatchList UL FOUND!')
    print(m.group(0)[:2000])
else:
    print('WatchList UL NOT FOUND')
    # Show what's around the area where WatchList should be
    idx = t.find('load_stream')
    if idx > -1:
        print(f'load_stream at {idx}')
        print(t[idx-200:idx+200])

# Also check for a separate div that might contain the WatchList
for kw in ['سيرفر', 'WatchList', 'data-embed-id', 'data-embed-url']:
    idx = t.find(kw)
    if idx > -1:
        print(f'\nFound "{kw}" at {idx}:')
        print(t[max(0,idx-100):idx+300])
