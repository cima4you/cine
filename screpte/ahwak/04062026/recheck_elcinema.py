import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8')
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US,en;q=0.5'})
s.get('https://www.elcinema.com/')
s.headers.update({'Referer': 'https://www.elcinema.com/'})

titles = [
    ('توبة', 'توبة 2022'),
    ('ظل', 'ظل 2022'),
    ('سكة سفر', 'سكة سفر 2022'),
    ('منحنى خطر', 'منحنى خطر 2022'),
    ('يوتيرن', 'يوتيرن 2022'),
    ('ازمة منتصف العمر', 'ازمة منتصف العمر 2022'),
    ('العاصفة', 'العاصفة 2022'),
]

for orig, query in titles:
    print('\n=== %s (query: %s) ===' % (orig, query))
    r = s.get('https://www.elcinema.com/search/', params={'q': query}, allow_redirects=True, timeout=15)
    matches = re.findall(r'href="(/work/\d+/)"[^>]*>\s*([^<]+)</a>', r.text)
    print('Results: %d' % len(matches))
    for href, title in matches[:5]:
        print('  %s | %s' % (title.strip()[:50], href))
        r2 = s.get('https://www.elcinema.com' + href, timeout=10)
        for m in re.finditer(r'<img[^>]*src="([^"]*)"', r2.text):
            src = m.group(1)
            if '_315x420' in src and 'uploads' in src:
                print('    Poster: %s' % src)
                break
        # Also check what elcinema shows as title/year
        ym = re.search(r'<span[^>]*class="year"[^>]*>(\d{4})', r2.text)
        if ym:
            print('    Year: %s' % ym.group(1))
