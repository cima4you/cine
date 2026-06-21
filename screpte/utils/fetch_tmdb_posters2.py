import json, os, sys, requests, re
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

missing = [(i, x) for i, x in enumerate(data) if x.get('type') == 'أجنبي' and 'tmdb' not in x.get('poster', '').lower()]
print(f'Missing: {len(missing)}')

def clean(t):
    t = re.sub(r'&#\d+;', '', t)
    t = re.sub(r'&[a-z]+;', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def try_search(idx, item):
    title = clean(item['title'])
    yr = re.search(r'(19\d\d|20\d\d)$', title)
    year = yr.group(1) if yr else None
    if year:
        title_stripped = title[:yr.start()].strip()
    else:
        title_stripped = title
    
    # Try movie search first
    params = {'api_key': API_KEY, 'query': title_stripped, 'language': 'en-US'}
    if year:
        params['primary_release_year'] = year
    
    try:
        r = requests.get(f'{BASE}/search/movie', params=params, timeout=10)
        if r.status_code == 200:
            results = r.json().get('results', [])
            if results:
                poster = results[0].get('poster_path')
                if poster:
                    return idx, f'https://image.tmdb.org/t/p/w500{poster}'
    except:
        pass
    
    # Try TV search (for series)
    try:
        r = requests.get(f'{BASE}/search/tv', params=params, timeout=10)
        if r.status_code == 200:
            results = r.json().get('results', [])
            if results:
                poster = results[0].get('poster_path')
                if poster:
                    return idx, f'https://image.tmdb.org/t/p/w500{poster}'
    except:
        pass
    
    # Try without year if year was present
    if yr:
        try:
            r = requests.get(f'{BASE}/search/movie', params={'api_key': API_KEY, 'query': title_stripped}, timeout=10)
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
    futures = {ex.submit(try_search, i, x): i for i, x in missing}
    for fut in as_completed(futures):
        idx, url = fut.result()
        if url:
            data[idx]['poster'] = url
            found += 1
        else:
            not_found += 1
        if (found + not_found) % 100 == 0:
            print(f'  {found+not_found}/{len(missing)}: found={found}')

print(f'\nSecond pass: found={found}, still missing={not_found}')

json_str = json.dumps(data, ensure_ascii=False)
with open(DATA_DIR, 'w', encoding='utf-8') as f:
    f.write(c[:arr_start] + json_str + c[arr_end:])
print('Saved.')
