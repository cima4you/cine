import requests, re, json, sys, urllib3
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
})
s.verify = False

# Explore search functionality
print('=== Test 1: Search "مسلسل 2025" ===')
r = s.get('https://www.elcinema.com/search/', params={'q': 'مسلسل 2025'}, timeout=15)
print(f'HTTP {r.status_code}, len={len(r.text)}')

# Check result links
work_links = re.findall(r'href="(/work/\d+/)"[^>]*>\s*([^<]+)', r.text)
print(f'Work links found: {len(work_links)}')
for href, name in work_links[:5]:
    print(f'  {name.strip()}: {href}')

# Check pagination
pagination = re.findall(r'href="[^"]*\?q=[^"]*page=(\d+)"', r.text)
print(f'Pagination pages: {pagination}')

# Check browse/year pages instead
print('\n=== Test 2: Browse by year ===')
# Try the browse page
r2 = s.get('https://www.elcinema.com/browse/series/', params={'year': '2025'}, timeout=15)
print(f'HTTP {r2.status_code}, len={len(r2.text)}')
work_links2 = re.findall(r'href="(/work/\d+/)"[^>]*>\s*([^<]+)', r2.text)
print(f'Work links: {len(work_links2)}')
for href, name in work_links2[:5]:
    print(f'  {name.strip()}: {href}')

# Check for "browse" URL pattern
print('\n=== Test 3: Browse series by year alternative ===')
for url in ['https://www.elcinema.com/browse/series/2025/',
            'https://www.elcinema.com/series/2025/',
            'https://www.elcinema.com/browse/year/2025/']:
    try:
        r3 = s.get(url, timeout=15)
        print(f'{url}: HTTP {r3.status_code}, len={len(r3.text)}')
        if r3.status_code == 200:
            links = re.findall(r'href="(/work/\d+/)"', r3.text)
            print(f'  Work links: {len(links)}')
    except Exception as e:
        print(f'{url}: ERROR {e}')

# Check search with filters
print('\n=== Test 4: Search with different keywords ===')
for q in ['مسلسل 2025', 'series 2025', '2025 مسلسلات']:
    r4 = s.get('https://www.elcinema.com/search/', params={'q': q}, timeout=15)
    links = re.findall(r'href="(/work/\d+/)"', r4.text)
    print(f'  q="{q}": HTTP {r4.status_code}, len={len(r4.text)}, links={len(links)}')
    if links:
        # Check first work page
        first = links[0]
        r5 = s.get(f'https://www.elcinema.com{first}', timeout=15)
        print(f'  First work page ({first}): HTTP {r5.status_code}')
        # Check for poster
        posters = re.findall(r'<img[^>]*src="([^"]*_315x420[^"]*)"', r5.text)
        if posters:
            print(f'  Poster: {posters[0][:80]}')
        # Check for title, year, type
        title_m = re.search(r'<h1[^>]*>([^<]+)', r5.text)
        year_m = re.search(r'(\d{4})', r5.text[:2000])
        print(f'  Title: {title_m.group(1).strip() if title_m else "N/A"}')
        print(f'  Year: {year_m.group(1) if year_m else "N/A"}')
        break
