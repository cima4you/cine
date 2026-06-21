#!/usr/bin/env python3
"""
Fetch elcinema.com posters for larozza.yachts Ramadan 2025 series.
Updates the results JSON file and then data.js.
"""
import requests, re, json, os, sys, time
sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_FILE = os.path.join(SCRIPT_DIR, 'data', 'results_yachts_13_ramadan_2025.json')
DATA_FILE = os.path.join(SCRIPT_DIR, '..', '..', 'data.js')

s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
})
s.get('https://www.elcinema.com/')
s.headers.update({'Referer': 'https://www.elcinema.com/'})

with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

total = len(data)
found = 0
not_found = 0
failed = 0

for i, series in enumerate(data):
    title = series['title']
    if series.get('poster') and 'elcinema' in series['poster'].lower():
        print(f'  [{i+1}/{total}] {title}... SKIP (already has elcinema poster)')
        found += 1
        continue

    print(f'  [{i+1}/{total}] {title}...', end=' ', flush=True)

    try:
        r = s.get('https://www.elcinema.com/search/', params={'q': title}, allow_redirects=True, timeout=15)
        if r.status_code != 200:
            failed += 1
            print(f'HTTP {r.status_code}')
            continue

        match = re.search(r'href="(/work/\d+/)"[^>]*>\s*([^<]+)</a>', r.text)
        if not match:
            not_found += 1
            print('no results')
            continue

        href = match.group(1)
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

        time.sleep(0.5)

    except Exception as e:
        failed += 1
        print(f'ERROR: {e}')

print(f'\nDone: {found} found, {not_found} not found, {failed} failed out of {total}')

with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'Saved to {RESULTS_FILE}')

# Build poster map
poster_map = {}
for s in data:
    title = s['title'].strip()
    poster = s.get('poster', '')
    if 'elcinema' in poster.lower():
        poster_map[title] = poster

print(f'\nUpdating data.js with {len(poster_map)} posters...')

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    content = f.read()
arr_start = content.index('[')
arr_end = content.rindex(']') + 1
existing = json.loads(content[arr_start:arr_end])
prefix = content[:arr_start]
suffix = content[arr_end:]

updated = 0
for item in existing:
    title = item.get('title', '').strip()
    if title in poster_map:
        old = item.get('poster', '')
        new = poster_map[title]
        if old != new:
            item['poster'] = new
            updated += 1

print(f'Updated {updated} posters in data.js ({len(existing)} total)')

json_str = json.dumps(existing, ensure_ascii=False)
with open(DATA_FILE, 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('Done.')
