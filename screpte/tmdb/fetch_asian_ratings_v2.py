import requests, json, re, time, html

TMDB_KEY = '0301bf9dd3a630dcbbea37f5c2b07d3e'
headers = {'User-Agent': 'Mozilla/5.0'}

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

asian = [(i, x) for i, x in enumerate(d) if x.get('type') == 'أسيوي']

# Find still-unrated
unrated = [(i, x) for i, x in asian if not x.get('rate') or float(x.get('rate', 0)) == 0]
print('Still unrated: {}'.format(len(unrated)))

def search_tmdb(title, year):
    url = 'https://api.themoviedb.org/3/search/movie'
    params = {'api_key': TMDB_KEY, 'query': title, 'language': 'en-US'}
    if year:
        params['year'] = year
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get('results'):
            for res in data['results']:
                res_year = res.get('release_date', '')[:4]
                if year and res_year == year:
                    rating = res.get('vote_average', 0)
                    tmdb_id = res.get('id')
                    imdb_id = None
                    if tmdb_id:
                        try:
                            detail = requests.get(
                                'https://api.themoviedb.org/3/movie/{}'.format(tmdb_id),
                                params={'api_key': TMDB_KEY}, timeout=10
                            )
                            if detail.status_code == 200:
                                imdb_id = detail.json().get('imdb_id')
                        except:
                            pass
                    return rating, imdb_id
            rating = data['results'][0].get('vote_average', 0)
            tmdb_id = data['results'][0].get('id')
            imdb_id = None
            if tmdb_id:
                try:
                    detail = requests.get(
                        'https://api.themoviedb.org/3/movie/{}'.format(tmdb_id),
                        params={'api_key': TMDB_KEY}, timeout=10
                    )
                    if detail.status_code == 200:
                        imdb_id = detail.json().get('imdb_id')
                except:
                    pass
            return rating, imdb_id
    except:
        pass
    return None

results = []
for idx, (orig_i, item) in enumerate(unrated):
    title_raw = item.get('title', '').strip()
    
    # Decode HTML entities
    title = html.unescape(title_raw)
    year = str(item.get('year', ''))
    
    # Strip trailing year if title ends with year
    title_clean = re.sub(r'\s+\d{4}$', '', title)
    
    found = False
    
    # Try 1: clean title + year
    res = search_tmdb(title_clean, year)
    if res:
        found = True
    
    # Try 2: clean title without year
    if not found and year:
        time.sleep(0.3)
        res = search_tmdb(title_clean, '')
        if res:
            found = True
    
    # Try 3: original title without year
    if not found and title_clean != title:
        time.sleep(0.3)
        res = search_tmdb(title, year)
        if res:
            found = True
    
    # Try 4: extract just primary title (before colon, dash etc)
    if not found:
        simpler = re.split(r'[:–\-]', title_clean)[0].strip()
        if simpler != title_clean and len(simpler) > 3:
            time.sleep(0.3)
            res = search_tmdb(simpler, year)
            if res:
                found = True
    
    # Try 5: just first word as fallback
    if not found:
        first_word = title_clean.split()[0] if title_clean.split() else ''
        if len(first_word) > 3:
            time.sleep(0.3)
            res = search_tmdb(first_word, year)
            if res:
                found = True
    
    if found:
        rating, imdb_id = res
        results.append({'idx': orig_i, 'title': title, 'year': year, 'rating': rating, 'imdb_id': imdb_id})
        print('  FOUND: "{}" ({}) -> rate={}, imdb={}'.format(title[:50], year, rating, imdb_id or '-'))
    else:
        print('  FAIL: "{}" ({})'.format(title[:60], year))
    
    time.sleep(0.35)

# Update
for r in results:
    idx = r['idx']
    if r['rating'] > 0:
        d[idx]['rate'] = str(round(r['rating'], 1))
    if r['imdb_id'] and not d[idx].get('imdb'):
        d[idx]['imdb'] = r['imdb_id']

print('\nSecond pass found: {}'.format(len(results)))

if results:
    prefix = content[:content.index('[')]
    suffix = content[content.rindex(']') + 1:]
    json_str = json.dumps(d, ensure_ascii=False)
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(prefix + json_str + suffix)
    print('Saved data.js')

# Final stats
asian_final = [x for x in d if x.get('type') == 'أسيوي']
with_rate = sum(1 for x in asian_final if x.get('rate') and float(x.get('rate', 0)) > 0)
print('\nFinal: {}/{} Asian movies have ratings'.format(with_rate, len(asian_final)))
