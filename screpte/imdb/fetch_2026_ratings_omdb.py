import json, requests, time

OMDB_KEY = 'dac33e2a'

with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
d = json.loads(c[c.index('['):c.rindex(']')+1])

asian2026_unrated = [x for x in d if x.get('type') == 'أسيوي' and x.get('year') == '2026' 
                     and (not x.get('rate') or float(x.get('rate', 0)) == 0)]

print('Unrated Asian 2026 movies: {}'.format(len(asian2026_unrated)))

for item in asian2026_unrated:
    title = item.get('title', '').strip()
    year = item.get('year', '')
    imdb = item.get('imdb', '')
    
    found = False
    
    # Try OMDb by IMDB ID
    if imdb:
        try:
            r = requests.get('http://www.omdbapi.com/?i={}&apikey={}'.format(imdb, OMDB_KEY), timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get('Response') == 'True' and data.get('imdbRating') and data['imdbRating'] != 'N/A':
                    rating = float(data['imdbRating'])
                    item['rate'] = str(rating)
                    print('  OMDb IMDB: "{}" -> rate={}'.format(title[:50], rating))
                    found = True
        except:
            pass
        time.sleep(0.3)
    
    # Try OMDb by title
    if not found:
        try:
            r = requests.get('http://www.omdbapi.com/?t={}&y={}&apikey={}'.format(title, year, OMDB_KEY), timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get('Response') == 'True' and data.get('imdbRating') and data['imdbRating'] != 'N/A':
                    rating = float(data['imdbRating'])
                    item['rate'] = str(rating)
                    if data.get('imdbID') and data['imdbID'] != 'N/A':
                        item['imdb'] = data['imdbID']
                    print('  OMDb title: "{}" -> rate={}, imdb={}'.format(title[:50], rating, data.get('imdbID','')))
                    found = True
        except:
            pass
        time.sleep(0.3)
    
    if not found:
        print('  FAIL: "{}" (imdb={})'.format(title[:50], imdb or '-'))

# Save
prefix = c[:c.index('[')]
suffix = c[c.rindex(']') + 1:]
json_str = json.dumps(d, ensure_ascii=False)
with open('data.js', 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)

# Final check
final = [x for x in d if x.get('type') == 'أسيوي' and x.get('year') == '2026']
still_unrated = [x for x in final if not x.get('rate') or float(x.get('rate', 0)) == 0]
print('\nStill unrated: {} / {}'.format(len(still_unrated), len(final)))
for x in still_unrated:
    print('  "{}"'.format(x.get('title','').strip()))
