import re, cloudscraper

scraper = cloudscraper.create_scraper()

vid = '19997b01f'
r = scraper.get(f'https://cimafre.site/watch.php?vid={vid}', timeout=30)
r.encoding = 'utf-8'
t = r.text
print(f'Status: {r.status_code}, size: {len(t)} bytes')

# Check for WatchList
m = re.search(r'<ul[^>]*class="[^"]*WatchList[^"]*"[^>]*>.*?</ul>', t, re.DOTALL)
if m:
    print('\nWatchList UL FOUND!')
    print(m.group(0))
else:
    print('\nWatchList UL NOT FOUND')

# Also check DownloadList
m2 = re.search(r'<ul[^>]*class="[^"]*DownloadList[^"]*"[^>]*>.*?</ul>', t, re.DOTALL)
if m2:
    print('\nDownloadList FOUND!')
    print(m2.group(0)[:1000])
else:
    print('\nDownloadList NOT FOUND')

# Save full HTML for analysis
with open('screpte/cimafre/data/cloudflare_detail.html', 'w', encoding='utf-8') as f:
    f.write(t)
print('\nSaved to cloudflare_detail.html')
