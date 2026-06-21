import json, os, sys, requests, re, html
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding='utf-8')

API_KEY = '0301bf9dd3a630dcbbea37f5c2b07d3e'
BASE = 'https://api.themoviedb.org/3'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data.js')

with open(DATA_DIR, 'r', encoding='utf-8') as f:
    c = f.read()
arr_start = c.index('[')
arr_end = c.rindex(']') + 1
data = json.loads(c[arr_start:arr_end])
prefix = c[:arr_start]
suffix = c[arr_end:]

missing = [(i, x) for i, x in enumerate(data) if x.get('type') == 'أجنبي' and 'tmdb' not in x.get('poster', '').lower()]
print(f'Missing: {len(missing)}')

def smart_clean(title):
    t = html.unescape(title.strip())
    # Remove year at end
    yr = re.search(r'\s+(19\d\d|20\d\d)$', t)
    year = yr.group(1) if yr else None
    if year:
        t = t[:yr.start()].strip()
    # Remove trailing numbers that look like episode/season markers
    t = re.sub(r'\s+(?:Part|Season|Volume|Vol|Chapter|Episode|Ep)\s*\d+.*$', '', t, flags=re.I)
    t = re.sub(r'\s+\d+\s*$', '', t)
    # Remove very short trailing noise
    t = re.sub(r'\s+[!@#$%^&*()]+\s*$', '', t)
    return t.strip(), year

def multi_search(idx, item):
    raw = html.unescape(item['title'].strip())
    title, year = smart_clean(raw)
    if not title or len(title) < 2:
        return idx, None
    
    params = {'api_key': API_KEY, 'query': title, 'language': 'en-US', 'include_adult': True}
    if year:
        params['primary_release_year'] = year
    
    for endpoint in ['search/multi', 'search/movie', 'search/tv']:
        try:
            r = requests.get(f'{BASE}/{endpoint}', params=params, timeout=10)
            if r.status_code == 200:
                results = r.json().get('results', [])
                if results:
                    found_title = results[0].get('title', results[0].get('name', ''))
                    # Skip if clearly wrong match
                    poster = results[0].get('poster_path')
                    if poster and found_title:
                        return idx, f'https://image.tmdb.org/t/p/w500{poster}'
        except:
            pass
    
    # Try without year
    if year:
        params.pop('primary_release_year', None)
        for endpoint in ['search/multi', 'search/movie', 'search/tv']:
            try:
                r = requests.get(f'{BASE}/{endpoint}', params=params, timeout=10)
                if r.status_code == 200:
                    results = r.json().get('results', [])
                    if results:
                        poster = results[0].get('poster_path')
                        if poster:
                            return idx, f'https://image.tmdb.org/t/p/w500{poster}'
            except:
                pass
    
    return idx, None

found = 0
not_found = 0
with ThreadPoolExecutor(max_workers=10) as ex:
    futures = {ex.submit(multi_search, i, x): i for i, x in missing}
    for fut in as_completed(futures):
        idx, url = fut.result()
        if url:
            data[idx]['poster'] = url
            found += 1
        else:
            not_found += 1
        if (found + not_found) % 20 == 0:
            print(f'  {found+not_found}/{len(missing)}: found={found}')

print(f'\nFourth pass: found={found}, still missing={not_found}')

json_str = json.dumps(data, ensure_ascii=False)
with open(DATA_DIR, 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('Saved.')
