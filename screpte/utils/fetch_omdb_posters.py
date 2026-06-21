import json, sys, requests, html, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding='utf-8')

API_KEY = 'dac33e2a'
BASE_DIR = '.'
DATA_JS = 'data.js'

with open(DATA_JS, 'r', encoding='utf-8') as f:
    c = f.read()
arr_start = c.index('[')
arr_end = c.rindex(']') + 1
data = json.loads(c[arr_start:arr_end])
prefix = c[:arr_start]
suffix = c[arr_end:]

missing = [(i, x) for i, x in enumerate(data) if x.get('type') == 'أجنبي' and 'tmdb' not in x.get('poster', '').lower()]
print(f'Missing from TMDB: {len(missing)}')

def clean_title(title):
    t = html.unescape(title.strip())
    yr = re.search(r'\s+(19\d\d|20\d\d)$', t)
    year = yr.group(1) if yr else None
    if year:
        t = t[:yr.start()].strip()
    t = re.sub(r'\s+(?:Part|Season|Volume|Vol|Chapter|Episode|Ep)\s*\d+.*$', '', t, flags=re.I)
    t = re.sub(r'\s+[\-–—]\s+\d+\s*$', '', t)
    t = re.sub(r'\s+\d+\s*$', '', t)
    return t.strip(), year

def omdb_search(idx, item):
    raw = html.unescape(item['title'].strip())
    title, year = clean_title(raw)
    if not title or len(title) < 2:
        return idx, None
    
    params = {'apikey': API_KEY, 't': title, 'plot': 'short'}
    if year:
        params['y'] = year
    
    try:
        r = requests.get('https://www.omdbapi.com/', params=params, timeout=10)
        if r.status_code == 200:
            j = r.json()
            if j.get('Response') == 'True' and j.get('Poster') and j['Poster'] != 'N/A':
                return idx, j['Poster']
    except:
        pass
    
    # Try without year
    if year:
        params.pop('y', None)
        try:
            r = requests.get('https://www.omdbapi.com/', params=params, timeout=10)
            if r.status_code == 200:
                j = r.json()
                if j.get('Response') == 'True' and j.get('Poster') and j['Poster'] != 'N/A':
                    return idx, j['Poster']
        except:
            pass
    
    return idx, None

found = 0
not_found = 0
# OMDb free tier: 1k/day, use sequential to be safe
for i, x in missing:
    idx, url = omdb_search(i, x)
    if url:
        data[idx]['poster'] = url
        found += 1
        print(f'  FOUND: {x["title"]} -> {url[:60]}')
    else:
        not_found += 1
    if (found + not_found) % 10 == 0:
        print(f'  Progress: {found+not_found}/{len(missing)}: found={found}')
    time.sleep(0.2)

print(f'\nOMDb results: found={found}, still missing={not_found}')

json_str = json.dumps(data, ensure_ascii=False)
with open(DATA_JS, 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('Saved.')
