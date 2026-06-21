import json, os, sys, requests, re, html, time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding='utf-8')

TMDB_KEY = '0301bf9dd3a630dcbbea37f5c2b07d3e'
OMDB_KEY = 'dac33e2a'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_JS = os.path.join(BASE_DIR, 'data.js')

with open(DATA_JS, 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])
prefix = c[:c.index('[')]
suffix = c[c.rindex(']')+1:]

# Find items with egydead.live posters
targets = [(i, x) for i, x in enumerate(data) if 'egydead.live' in x.get('poster', '')]
print('Found %d items with egydead.live posters' % len(targets))

def clean_title(title):
    t = html.unescape(title.strip())
    yr = re.search(r'\s+(19\d\d|20\d\d)$', t)
    year = yr.group(1) if yr else None
    if year:
        t = t[:yr.start()].strip()
    t = re.sub(r'\s+(?:Part|Season|Volume|Vol|Chapter|Episode|Ep)\s*\d+.*$', '', t, flags=re.I)
    t = re.sub(r'\s+\d+\s*$', '', t)
    return t.strip(), year

def find_poster(idx, item):
    raw = html.unescape(item['title'].strip())
    title, year = clean_title(raw)
    if not title or len(title) < 2:
        return idx, None
    
    # Try TMDB
    params = {'api_key': TMDB_KEY, 'query': title, 'language': 'en-US', 'include_adult': True}
    if year:
        params['primary_release_year'] = year
    
    for endpoint in ['search/multi', 'search/movie', 'search/tv']:
        try:
            r = requests.get(f'https://api.themoviedb.org/3/{endpoint}', params=params, timeout=10)
            if r.status_code == 200:
                results = r.json().get('results', [])
                if results:
                    poster = results[0].get('poster_path')
                    if poster:
                        return idx, f'https://image.tmdb.org/t/p/w500{poster}'
        except:
            pass
    
    if year:
        params.pop('primary_release_year', None)
        for endpoint in ['search/multi', 'search/movie', 'search/tv']:
            try:
                r = requests.get(f'https://api.themoviedb.org/3/{endpoint}', params=params, timeout=10)
                if r.status_code == 200:
                    results = r.json().get('results', [])
                    if results:
                        poster = results[0].get('poster_path')
                        if poster:
                            return idx, f'https://image.tmdb.org/t/p/w500{poster}'
            except:
                pass
    
    # Fallback to OMDb
    try:
        omdb_params = {'apikey': OMDB_KEY, 't': title}
        if year:
            omdb_params['y'] = year
        r = requests.get('https://www.omdbapi.com/', params=omdb_params, timeout=10)
        if r.status_code == 200:
            data_r = r.json()
            if data_r.get('Response') == 'True' and data_r.get('Poster') and data_r['Poster'] != 'N/A':
                return idx, data_r['Poster']
    except:
        pass
    
    if year:
        try:
            r = requests.get('https://www.omdbapi.com/', params={'apikey': OMDB_KEY, 't': title}, timeout=10)
            if r.status_code == 200:
                data_r = r.json()
                if data_r.get('Response') == 'True' and data_r.get('Poster') and data_r['Poster'] != 'N/A':
                    return idx, data_r['Poster']
        except:
            pass
    
    return idx, None

found = 0
not_found = 0
with ThreadPoolExecutor(max_workers=10) as ex:
    futures = {ex.submit(find_poster, i, x): i for i, x in targets}
    for fut in as_completed(futures):
        idx, url = fut.result()
        if url:
            old = data[idx]['poster'][:40]
            data[idx]['poster'] = url
            found += 1
        else:
            not_found += 1
        if (found + not_found) % 20 == 0:
            print('  %d/%d: found=%d, not_found=%d' % (found+not_found, len(targets), found, not_found))
        time.sleep(0.05)

print('\nDone: found=%d, not_found=%d out of %d' % (found, not_found, len(targets)))

json_str = json.dumps(data, ensure_ascii=False)
with open(DATA_JS, 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('data.js saved')
