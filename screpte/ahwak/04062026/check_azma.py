import requests, re, sys, time
sys.stdout.reconfigure(encoding='utf-8')
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US,en;q=0.5'})
s.get('https://www.elcinema.com/')
s.headers.update({'Referer': 'https://www.elcinema.com/'})

# Check ازمة منتصف العمر more carefully
for q in ['أزمة منتصف العمر مسلسل', 'ازمة منتصف العمر']:
    print('\n=== %s ===' % q)
    r = s.get('https://www.elcinema.com/search/', params={'q': q}, allow_redirects=True, timeout=15)
    matches = re.findall(r'href="(/work/\d+/)"[^>]*>\s*([^<]+)</a>', r.text)
    for href, t in matches:
        t2 = t.strip()
        if re.match(r'^[a-zA-Z\s\d]+$', t2):
            continue
        r2 = s.get('https://www.elcinema.com' + href, timeout=10)
        tm = re.search(r'<title>([^<]+)</title>', r2.text)
        title_tag = tm.group(1)[:80] if tm else '?'
        poster = None
        for m in re.finditer(r'<img[^>]*src="([^"]*)"', r2.text):
            src = m.group(1)
            if '_315x420' in src and 'uploads' in src:
                poster = src
                break
        print('  %s | %s | %s | %s' % (t2[:40], href, title_tag[:60], poster[:100] if poster else 'none'))
        time.sleep(0.5)
