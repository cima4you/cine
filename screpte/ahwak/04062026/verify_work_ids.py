import requests, re, sys, time
sys.stdout.reconfigure(encoding='utf-8')
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US,en;q=0.5'})
s.get('https://www.elcinema.com/')
s.headers.update({'Referer': 'https://www.elcinema.com/'})

work_ids = {
    'توبة': None,
    'ظل': None,
    'سكة سفر': '2073681',
    'منحنى خطر': None,
    'يوتيرن': '2072354',
    'ازمة منتصف العمر': '2075848',
    'العاصفة': '1442564',
}

# First verify the ones we have IDs for
for title, wid in work_ids.items():
    if not wid:
        print('\n=== %s: no ID yet ===' % title)
        # Search specifically
        r = s.get('https://www.elcinema.com/search/', params={'q': 'مسلسل ' + title + ' 2022'}, allow_redirects=True, timeout=15)
        matches = re.findall(r'href="(/work/\d+/)"[^>]*>\s*([^<]+)</a>', r.text)
        for href, t in matches:
            t2 = t.strip()
            if re.match(r'^[a-zA-Z\s\d]+$', t2):
                continue
            r2 = s.get('https://www.elcinema.com' + href, timeout=10)
            ym = re.search(r'<span[^>]*class="year"[^>]*>(\d{4})', r2.text)
            year = ym.group(1) if ym else '?'
            poster = None
            for m in re.finditer(r'<img[^>]*src="([^"]*)"', r2.text):
                src = m.group(1)
                if '_315x420' in src and 'uploads' in src:
                    poster = src
                    break
            print('  %s | year=%s | %s' % (t2[:50], year, poster[:100] if poster else 'none'))
            time.sleep(0.5)
        continue
    
    r2 = s.get('https://www.elcinema.com/work/%s/' % wid, timeout=15)
    ym = re.search(r'<span[^>]*class="year"[^>]*>(\d{4})', r2.text)
    year = ym.group(1) if ym else '?'
    poster = None
    for m in re.finditer(r'<img[^>]*src="([^"]*)"', r2.text):
        src = m.group(1)
        if '_315x420' in src and 'uploads' in src:
            poster = src
            break
    print('\n=== %s (work/%s) ===' % (title, wid))
    print('  year=%s' % year)
    print('  poster=%s' % (poster[:120] if poster else 'none'))
    # Also check page title
    tm = re.search(r'<title>([^<]+)</title>', r2.text)
    if tm:
        print('  title=%s' % tm.group(1)[:80])
    time.sleep(0.5)
