import requests, json, re, time

TMDB_KEY = '0301bf9dd3a630dcbbea37f5c2b07d3e'
headers = {'User-Agent': 'Mozilla/5.0'}

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

asian = [(i, x) for i, x in enumerate(d) if x.get('type') == 'أسيوي']
print('Asian movies needing ratings: {}'.format(len(asian)))

def search_tmdb(title, year):
    """Search TMDb by title+year, return (rating, imdb_id) or None"""
    url = 'https://api.themoviedb.org/3/search/movie'
    params = {
        'api_key': TMDB_KEY,
        'query': title,
        'year': year,
        'language': 'en-US'
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return None
        data = r.json()
        if data.get('results'):
            # Try to find exact year match
            for res in data['results']:
                res_year = res.get('release_date', '')[:4]
                if res_year == year:
                    rating = res.get('vote_average', 0)
                    tmdb_id = res.get('id')
                    # Get IMDB ID
                    imdb_id = None
                    if tmdb_id:
                        try:
                            detail = requests.get(
                                'https://api.themoviedb.org/3/movie/{}'.format(tmdb_id),
                                params={'api_key': TMDB_KEY},
                                timeout=10
                            )
                            if detail.status_code == 200:
                                imdb_id = detail.json().get('imdb_id')
                        except:
                            pass
                    return rating, imdb_id
            # Fallback to first result
            rating = data['results'][0].get('vote_average', 0)
            tmdb_id = data['results'][0].get('id')
            imdb_id = None
            if tmdb_id:
                try:
                    detail = requests.get(
                        'https://api.themoviedb.org/3/movie/{}'.format(tmdb_id),
                        params={'api_key': TMDB_KEY},
                        timeout=10
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
for asian_idx, (orig_idx, item) in enumerate(asian):
    title = item.get('title', '').strip()
    year = str(item.get('year', ''))
    
    # Try with original title
    res = search_tmdb(title, year)
    
    # Try without year
    if not res and year:
        time.sleep(0.3)
        res = search_tmdb(title, '')
    
    if res:
        rating, imdb_id = res
        results.append({
            'idx': orig_idx,
            'title': title,
            'year': year,
            'rating': rating,
            'imdb_id': imdb_id
        })
        print('  [{}/{}] "{}" -> rating={}, imdb={}'.format(asian_idx+1, len(asian), title[:40], rating, imdb_id or '-'))
    else:
        print('  [{}/{}] "{}" -> NOT FOUND'.format(asian_idx+1, len(asian), title[:40]))
    
    time.sleep(0.35)

# Update data.js
updated = 0
for r in results:
    idx = r['idx']
    rating = r['rating']
    imdb_id = r['imdb_id']
    if rating > 0:
        d[idx]['rate'] = str(round(rating, 1))
    if imdb_id and not d[idx].get('imdb'):
        d[idx]['imdb'] = imdb_id
    updated += 1

print('\nTotal found: {}'.format(len(results)))
print('Updated: {}'.format(updated))

if updated > 0:
    prefix = content[:content.index('[')]
    suffix = content[content.rindex(']') + 1:]
    json_str = json.dumps(d, ensure_ascii=False)
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(prefix + json_str + suffix)
    print('Saved data.js')
