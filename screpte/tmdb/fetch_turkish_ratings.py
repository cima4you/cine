import json, re, requests, time, sys

TMDB_KEY = '0301bf9dd3a630dcbbea37f5c2b07d3e'

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

turkish = [(i, x) for i, x in enumerate(d) if x.get('type') == 'تركي']
print('Turkish movies: {}'.format(len(turkish)))

# Check ratings
have_rating = sum(1 for _, x in turkish if x.get('rating') and float(x.get('rating', 0)) > 0)
have_imdb = sum(1 for _, x in turkish if x.get('imdbID'))
print('With rating > 0: {}'.format(have_rating))
print('With imdbID: {}'.format(have_imdb))

# Fetch ratings from TMDb
def search_tmdb(title, year):
    url = 'https://api.themoviedb.org/3/search/movie'
    params = {'api_key': TMDB_KEY, 'query': title, 'year': year, 'language': 'en-US'}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data['results']:
                movie = data['results'][0]
                # Get IMDB ID from TMDb
                mid = movie['id']
                det = requests.get('https://api.themoviedb.org/3/movie/{}'.format(mid),
                                   params={'api_key': TMDB_KEY}, timeout=10).json()
                imdb_id = det.get('imdb_id', '')
                vote = movie.get('vote_average', 0)
                # Convert TMDb rating to IMDB-like (10-scale to 10-scale)
                rating = round(vote, 1) if vote > 0 else 0.0
                return rating, imdb_id
    except:
        pass
    return 0.0, ''

updated = 0
failed = 0
for idx, item in turkish:
    title = item.get('title', '').strip()
    year = str(item.get('year', ''))
    
    # Skip if already has rating
    if item.get('rating') and float(item.get('rating', 0)) > 0:
        continue
    
    # Clean title for search
    search_title = re.sub(r'\s+\d{4}$', '', title)
    
    rating, imdb_id = search_tmdb(search_title, year)
    if rating > 0:
        d[idx]['rating'] = rating
        updated += 1
        print('  RATING {}: "{}" ({})'.format(rating, title[:40], year))
    if imdb_id and not item.get('imdbID'):
        d[idx]['imdbID'] = imdb_id
    
    if rating == 0 and not imdb_id:
        failed += 1
        if failed <= 5:
            print('  NO RATING: "{}" ({})'.format(title[:40], year))
    
    # Rate limit
    time.sleep(0.35)

if updated > 0:
    prefix = content[:content.index('[')]
    suffix = content[content.rindex(']') + 1:]
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(prefix + json.dumps(d, ensure_ascii=False) + suffix)
    print('\nUpdated ratings: {}'.format(updated))

# Final stats
turkish2 = [(i, x) for i, x in enumerate(d) if x.get('type') == 'تركي']
have_rating2 = sum(1 for _, x in turkish2 if x.get('rating') and float(x.get('rating', 0)) > 0)
have_imdb2 = sum(1 for _, x in turkish2 if x.get('imdbID'))
print('\nFinal: {} Turkish movies'.format(len(turkish2)))
print('With rating: {}'.format(have_rating2))
print('With imdbID: {}'.format(have_imdb2))
