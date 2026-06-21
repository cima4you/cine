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

# Check the advanced search /search/work/ URL with various params
print('=== Explore /search/work/ ===')
r = s.get('https://www.elcinema.com/search/work/', params={'q': 'مسلسل'}, timeout=15)
print(f'q=مسلسل: HTTP {r.status_code}, len={len(r.text)}')
if r.status_code == 200:
    links = re.findall(r'href="(/work/\d+/)"', r.text)
    print(f'  Work links: {len(links)}')
    # Check pagination
    pages = re.findall(r'href="[^"]*page=(\d+)"', r.text)
    print(f'  Pages: {pages}')

# Try empty search
r2 = s.get('https://www.elcinema.com/search/work/', timeout=15)
print(f'\nNo query: HTTP {r2.status_code}, len={len(r2.text)}')

# Try with minimum 2-letter query
r3 = s.get('https://www.elcinema.com/search/work/', params={'q': 'مس'}, timeout=15)
print(f'\nq=مس: HTTP {r3.status_code}, len={len(r3.text)}')

# Check if there's a year filter in the URL
r4 = s.get('https://www.elcinema.com/search/work/', params={'q': '2025', 'type': 'series'}, timeout=15)
print(f'\nq=2025 type=series: HTTP {r4.status_code}, len={len(r4.text)}')

# Try with type=series parameter  
r5 = s.get('https://www.elcinema.com/search/work/', params={'q': 'مسلسل', 'type': 'series'}, timeout=15)
print(f'\nq=مسلسل type=series: HTTP {r5.status_code}, len={len(r5.text)}')

# Check what the search/work page looks like
print('\n=== Search/work page structure ===')
if r4.status_code == 200:
    # Look for filters/forms
    selects = re.findall(r'<select[^>]*name="([^"]*)"', r4.text)
    print(f'  Selects found: {selects}')
    inputs = re.findall(r'<input[^>]*name="([^"]*)"', r4.text)
    print(f'  Inputs: {inputs[:15]}')

# Check /series/ pages
print('\n=== Explore /series/ ===')
r6 = s.get('https://www.elcinema.com/series/', timeout=15)
print(f'HTTP {r6.status_code}, len={len(r6.text)}')
if r6.status_code == 200:
    links = re.findall(r'href="(/work/\d+/)"', r6.text)
    print(f'  Work links: {len(links)}')

# Check pagination in search results
r7 = s.get('https://www.elcinema.com/search/work/', params={'q': 'مسلسل', 'page': 2}, timeout=15)
print(f'\nq=مسلسل page=2: HTTP {r7.status_code}, len={len(r7.text)}')
