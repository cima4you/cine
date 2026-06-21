import json, re, requests, time

TMDB_KEY = '0301bf9dd3a630dcbbea37f5c2b07d3e'

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

netflix = [(i, x) for i, x in enumerate(d) if x.get('type') == 'نتفليكس']
print('Netflix movies: {}'.format(len(netflix)))

def get_rating(x):
    r = x.get('rating', 0)
    if not r or r == 'N/A':
        return 0
    try:
        return float(r)
    except:
        return 0

have_rating = sum(1 for _, x in netflix if get_rating(x) > 0)
print('With rating > 0: {}'.format(have_rating))

updated = 0
for idx, item in netflix:
    if get_rating(item) > 0:
        continue
    
    title = re.sub(r'\s+\d{4}$', '', item.get('title', '').strip())
    year = str(item.get('year', ''))
    
    url = 'https://api.themoviedb.org/3/search/movie'
    params = {'api_key': TMDB_KEY, 'query': title, 'year': year, 'language': 'en-US'}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200 and r.json()['results']:
            movie = r.json()['results'][0]
            vote = movie.get('vote_average', 0)
            if vote > 0:
                d[idx]['rating'] = round(vote, 1)
                updated += 1
                print('  RATING {}: "{}" ({})'.format(round(vote,1), item.get('title','').strip()[:40], year))
            
            # Get imdbID
            mid = movie['id']
            det = requests.get('https://api.themoviedb.org/3/movie/{}'.format(mid),
                               params={'api_key': TMDB_KEY}, timeout=10).json()
            imdb_id = det.get('imdb_id', '')
            if imdb_id and not item.get('imdbID'):
                d[idx]['imdbID'] = imdb_id
    except:
        pass
    time.sleep(0.35)

if updated > 0:
    prefix = content[:content.index('[')]
    suffix = content[content.rindex(']') + 1:]
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(prefix + json.dumps(d, ensure_ascii=False) + suffix)
    print('\nUpdated ratings: {}'.format(updated))

netflix2 = [(i, x) for i, x in enumerate(d) if x.get('type') == 'نتفليكس']
have_rating2 = sum(1 for _, x in netflix2 if x.get('rating') and float(x.get('rating', 0)) > 0)
have_imdb2 = sum(1 for _, x in netflix2 if x.get('imdbID'))
print('\nFinal: {} Netflix, {} with rating, {} with imdbID'.format(len(netflix2), have_rating2, have_imdb2))
