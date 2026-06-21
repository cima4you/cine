import requests, re, sys, urllib3
sys.stdout.reconfigure(encoding='utf-8')
urllib3.disable_warnings()

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
    'Referer': 'https://www.elcinema.com/',
})
s.verify = False
s.get('https://www.elcinema.com/', timeout=15)

# Get search results
r = s.get('https://www.elcinema.com/search/', params={'q': 'مسلسل رامز ايلون مصر'}, timeout=15)
print(f'Search: HTTP {r.status_code}')

# Find all work link patterns
work_patterns = re.findall(r'href="(/[^"]*)"[^>]*>([^<]+)', r.text)
work_links = [(h, n.strip()) for h, n in work_patterns if '/work/' in h or '/movie/' in h or '/series/' in h]
print(f'\nWork-related links: {len(work_links)}')
for h, n in work_links[:10]:
    print(f'  {n}: {h}')

# Try the first work link
if work_links:
    href = work_links[0][0]
    if not href.startswith('http'):
        href = 'https://www.elcinema.com' + href
    r2 = s.get(href, timeout=15)
    print(f'\nWork page {href}: HTTP {r2.status_code}, len={len(r2.text)}')
    if r2.status_code == 200:
        # Save for analysis
        with open('elcinema_work.html', 'w', encoding='utf-8') as f:
            f.write(r2.text)
        poster = re.search(r'<img[^>]*src="([^"]*_315x420[^"]*)"', r2.text)
        print(f'  Poster: {poster.group(1)[:100] if poster else "N/A"}')
        title = re.search(r'<h1[^>]*>([^<]+)', r2.text)
        print(f'  Title: {title.group(1).strip() if title else "N/A"}')
    elif r2.status_code == 404:
        # Try without domain prefix
        print('  404 - maybe work pages need different pattern')

# Check if there's another pattern for work pages
print('\n=== Alternate work page patterns ===')
for href, name in work_links[:5]:
    if not href.startswith('/work/'):
        continue
    # Try different patterns like /ar/work/ or /en/work/
    for prefix in ['', '/ar', '/en']:
        url = f'https://www.elcinema.com{prefix}{href}'
        try:
            r3 = s.get(url, timeout=15)
            print(f'  {url}: HTTP {r3.status_code}')
            if r3.status_code == 200:
                poster = re.search(r'<img[^>]*src="([^"]*_315x420[^"]*)"', r3.text)
                print(f'    Poster found: {bool(poster)}')
                break
        except:
            pass
