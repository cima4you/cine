import requests, re, sys, json
sys.stdout.reconfigure(encoding='utf-8')
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US,en;q=0.5'})
s.get('https://www.elcinema.com/')
s.headers.update({'Referer': 'https://www.elcinema.com/'})

# Each: (title, queries_to_try)
items = [
    ('توبة', ['مسلسل توبة', 'توبة مسلسل 2022', 'توبة 2022']),
    ('ظل', ['مسلسل ظل', 'ظل مسلسل 2022']),
    ('سكة سفر', ['مسلسل سكة سفر', 'سكة سفر مسلسل']),
    ('منحنى خطر', ['مسلسل منحنى خطر', 'منحنى خطر مسلسل']),
    ('يوتيرن', ['مسلسل يوتيرن', 'يوتيرن مسلسل']),
    ('ازمة منتصف العمر', ['مسلسل ازمة منتصف العمر', 'أزمة منتصف العمر مسلسل', 'أزمة منتصف العمر']),
    ('العاصفة', ['مسلسل العاصفة', 'العاصفة مسلسل', 'عاصفة مسلسل']),
]

for orig, queries in items:
    print('\n=== %s ===' % orig)
    found = False
    for q in queries:
        if found: break
        r = s.get('https://www.elcinema.com/search/', params={'q': q}, allow_redirects=True, timeout=15)
        matches = re.findall(r'href="(/work/\d+/)"[^>]*>\s*([^<]+)</a>', r.text)
        # Filter: only Arabic titles that roughly match
        for href, title in matches:
            t = title.strip()
            # Check year
            r2 = s.get('https://www.elcinema.com' + href, timeout=10)
            ym = re.search(r'<span[^>]*class="year"[^>]*>(\d{4})', r2.text)
            year = ym.group(1) if ym else '?'
            
            # Check type: is it a series?
            # Get poster
            poster = None
            for m in re.finditer(r'<img[^>]*src="([^"]*)"', r2.text):
                src = m.group(1)
                if '_315x420' in src and 'uploads' in src:
                    poster = src
                    break
            
            # We need the user to tell us which one, but let's show what we find
            if t == orig or orig in t or t in orig:
                print('  MATCH by name: %s | %s | year=%s | %s' % (t, href, year, poster[:90] if poster else 'no poster'))
                if year == '2022':
                    print('    >> Likely correct (matched + 2022)')
                    found = True
            elif 'مسلسل' not in t and len(t) > 3:
                # Show non-English results  
                if not re.match(r'^[a-zA-Z\s]+$', t):
                    print('  Arabic result: %s | %s | year=%s' % (t, href, year))
    
    if not found:
        r = s.get('https://www.elcinema.com/search/', params={'q': orig}, allow_redirects=True, timeout=15)
        matches = re.findall(r'href="(/work/\d+/)"[^>]*>\s*([^<]+)</a>', r.text)
        for href, title in matches:
            t = title.strip()
            if not re.match(r'^[a-zA-Z\s\d]+$', t):
                r2 = s.get('https://www.elcinema.com' + href, timeout=10)
                ym = re.search(r'<span[^>]*class="year"[^>]*>(\d{4})', r2.text)
                year = ym.group(1) if ym else '?'
                poster = None
                for m in re.finditer(r'<img[^>]*src="([^"]*)"', r2.text):
                    src = m.group(1)
                    if '_315x420' in src and 'uploads' in src:
                        poster = src
                        break
                print('  Arabic: %s | %s | year=%s | %s' % (t, href, year, poster[:90] if poster else 'no poster'))
