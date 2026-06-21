import requests, re, sys, json, time
sys.stdout.reconfigure(encoding='utf-8')
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US,en;q=0.5'})
s.get('https://www.elcinema.com/')
s.headers.update({'Referer': 'https://www.elcinema.com/'})

def check(title, work_id=None):
    print('\n=== %s ===' % title)
    if work_id:
        r2 = s.get('https://www.elcinema.com/work/%s/' % work_id, timeout=15)
    else:
        r = s.get('https://www.elcinema.com/search/', params={'q': title}, allow_redirects=True, timeout=15)
        matches = re.findall(r'href="(/work/\d+/)"[^>]*>\s*([^<]+)</a>', r.text)
        print('Results:')
        for href, t in matches[:8]:
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
            print('  %s | year=%s | %s' % (t2[:40], year, poster[:100] if poster else 'none'))
            time.sleep(0.3)
        return
    
    ym = re.search(r'<span[^>]*class="year"[^>]*>(\d{4})', r2.text)
    year = ym.group(1) if ym else '?'
    poster = None
    for m in re.finditer(r'<img[^>]*src="([^"]*)"', r2.text):
        src = m.group(1)
        if '_315x420' in src and 'uploads' in src:
            poster = src
            break
    print('  Direct: year=%s | poster=%s' % (year, poster[:100] if poster else 'none'))

# Each item with known or suspected work IDs
# Based on previous search, but let's search properly
check('توبة')
time.sleep(1)
check('ظل')
time.sleep(1)
check('سكة سفر')
