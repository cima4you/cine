#!/usr/bin/env python3
"""
Fetch poster URLs from elcinema.com for all larozza series.
Replaces larozza.living poster URLs with elcinema ones.
"""
import requests, re, json, os, sys, time
sys.stdout.reconfigure(encoding='utf-8')

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
RESULTS_FILE = os.path.join(RESULTS_DIR, 'results_larozza_ramadan_2026.json')

with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
})

# Init session
s.get('https://www.elcinema.com/')
s.headers.update({'Referer': 'https://www.elcinema.com/'})

total = len(data)
found = 0
not_found = 0
failed = 0

for i, series in enumerate(data):
    title = series['title']
    old_poster = series.get('poster', '')
    
    # Skip if not from larozza
    if 'larozza' not in old_poster.lower():
        continue
    
    # Print progress
    print(f'  [{i+1}/{total}] {title}...', end=' ', flush=True)
    
    try:
        r = s.get('https://www.elcinema.com/search/', params={'q': title}, allow_redirects=True, timeout=15)
        
        if r.status_code != 200:
            failed += 1
            print(f'HTTP {r.status_code}')
            continue
        
        # Find first result title and link
        match = re.search(r'href="(/work/\d+/)"[^>]*>\s*([^<]+)</a>', r.text)
        if not match:
            not_found += 1
            print(f'no results')
            continue
        
        href, result_title = match.group(1), match.group(2).strip()
        
        # Visit work page for poster
        r2 = s.get(f'https://www.elcinema.com{href}', timeout=15)
        poster_src = None
        for m in re.finditer(r'<img[^>]*src="([^"]*)"', r2.text):
            src = m.group(1)
            if '_315x420' in src and 'uploads' in src:
                poster_src = src.replace('_315x420', '_810x1080')
                break
        
        if poster_src:
            data[i]['poster'] = poster_src
            found += 1
            print('OK')
        else:
            not_found += 1
            print('no poster')
        
        # Rate limit: small delay
        time.sleep(0.5)
        
    except Exception as e:
        failed += 1
        print(f'ERROR: {e}')

print(f'\nDone: {found} found, {not_found} not found, {failed} failed out of {total}')

# Save updated results
with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'Saved to {RESULTS_FILE}')
