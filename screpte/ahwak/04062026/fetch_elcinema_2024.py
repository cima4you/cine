import requests, re, json, os, sys, time
sys.stdout.reconfigure(encoding='utf-8')

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
RESULTS_FILE = os.path.join(DATA_DIR, 'results_yam_moslslat_ramadan_2024.json')

with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
})
s.get('https://www.elcinema.com/')
s.headers.update({'Referer': 'https://www.elcinema.com/'})

total = len(data)
found = 0
not_found = 0
failed = 0

for i, series in enumerate(data):
    title = series['title']
    old_poster = series.get('poster', '')

    if not old_poster:
        continue
    if 'tmdb' in old_poster.lower() or 'm.media-amazon' in old_poster.lower():
        continue
    if '.elcinema.com' in old_poster.lower():
        if '_810x1080' in old_poster:
            pass
        else:
            continue

    print('  [%d/%d] %s...' % (i+1, total, title), end=' ', flush=True)

    try:
        r = s.get('https://www.elcinema.com/search/', params={'q': title}, allow_redirects=True, timeout=15)

        if r.status_code != 200:
            failed += 1
            print('HTTP %d' % r.status_code)
            continue

        match = re.search(r'href="(/work/\d+/)"[^>]*>\s*([^<]+)</a>', r.text)
        if not match:
            not_found += 1
            print('no results')
            continue

        href, result_title = match.group(1), match.group(2).strip()

        r2 = s.get('https://www.elcinema.com' + href, timeout=15)
        poster_src = None
        for m in re.finditer(r'<img[^>]*src="([^"]*)"', r2.text):
            src = m.group(1)
            if '_315x420' in src and 'uploads' in src:
                poster_src = src
                break

        if poster_src:
            data[i]['poster'] = poster_src
            found += 1
            print('OK')
        else:
            not_found += 1
            print('no poster')

        time.sleep(0.5)

    except Exception as e:
        failed += 1
        print('ERROR: %s' % str(e))

print('\nDone: %d found, %d not found, %d failed out of %d' % (found, not_found, failed, total))

with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print('Saved to %s' % RESULTS_FILE)
