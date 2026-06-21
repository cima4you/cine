import cloudscraper, time

# Try with retry and different configs
for attempt in range(3):
    scraper = cloudscraper.create_scraper(
        delay=10,
        interpreter='native',
        allow_brotli=True,
    )
    
    # First request to home to get cookies
    r = scraper.get('https://tv8.egydead.live/', timeout=30)
    print('Attempt {}: Home status={}, len={}, blocked={}'.format(
        attempt + 1, r.status_code, len(r.text), 'Just a moment' in r.text or 'challenge' in r.text.lower()))
    
    if 'Just a moment' not in r.text and len(r.text) > 10000:
        print('SUCCESS!')
        break
    
    time.sleep(5)

# Also try with requests.Session + headers that match exactly
import requests

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
})

r2 = s.get('https://tv8.egydead.live/', timeout=30)
print('\nRequests Session: status={}, len={}, blocked={}'.format(
    r2.status_code, len(r2.text), 'Just a moment' in r2.text))
