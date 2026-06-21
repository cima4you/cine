import json, re, requests, time

TMDB_KEY = '0301bf9dd3a630dcbbea37f5c2b07d3e'

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

# Fix bad titles - remove entries with year-only titles
fixed = []
removed_count = 0
for item in d:
    title = item.get('title', '').strip()
    if re.match(r'^\d{4}$', title) and not item.get('servers'):
        # Remove these bad entries (no title, no servers)
        removed_count += 1
        continue
    # Clear false ratings on bad-title entries
    if re.match(r'^\d{4}$', title) and item.get('type') == 'تركي':
        item['rating'] = 0.0
    fixed.append(item)

print('Removed {} bad entries'.format(removed_count))
d = fixed

# Try to fetch ratings for those with imdbID but no rating
turkish = [(i, x) for i, x in enumerate(d) if x.get('type') == 'تركي']
no_rating_with_imdb = [(i, x) for i, x in turkish 
                       if x.get('imdbID') and (not x.get('rating') or float(x.get('rating', 0)) == 0)]

print('Turkish with imdbID but no rating: {}'.format(len(no_rating_with_imdb)))

for idx, item in no_rating_with_imdb:
    imdb_id = item['imdbID']
    # Try TMDb find by external ID
    url = 'https://api.themoviedb.org/3/find/{}'.format(imdb_id)
    params = {'api_key': TMDB_KEY, 'external_source': 'imdb_id'}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200 and r.json()['movie_results']:
            movie = r.json()['movie_results'][0]
            vote = movie.get('vote_average', 0)
            if vote > 0:
                d[idx]['rating'] = round(vote, 1)
                print('  RATING {}: "{}" ({}) via IMDB ID'.format(round(vote,1), item.get('title','').strip()[:40], item.get('year','')))
    except:
        pass
    time.sleep(0.35)

# Save
prefix = content[:content.index('[')]
suffix = content[content.rindex(']') + 1:]
with open('data.js', 'w', encoding='utf-8') as f:
    f.write(prefix + json.dumps(d, ensure_ascii=False) + suffix)

# Final
turkish2 = [(i, x) for i, x in enumerate(d) if x.get('type') == 'تركي']
have_rating = sum(1 for _, x in turkish2 if x.get('rating') and float(x.get('rating', 0)) > 0)
print('\nFinal: {} Turkish, {} with ratings'.format(len(turkish2), have_rating))
print('Total data.js: {}'.format(len(d)))
