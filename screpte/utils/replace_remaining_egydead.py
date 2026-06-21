import json, sys, requests, re, html, time
sys.stdout.reconfigure(encoding='utf-8')

TMDB_KEY = '0301bf9dd3a630dcbbea37f5c2b07d3e'
with open('data.js', 'r', encoding='utf-8') as f:
    c = f.read()
data = json.loads(c[c.index('['):c.rindex(']')+1])
prefix = c[:c.index('[')]
suffix = c[c.rindex(']')+1:]

remaining = [(i, x) for i, x in enumerate(data) if 'egydead.live' in x.get('poster', '')]
print('Trying harder for %d items...' % len(remaining))

def clean_harder(title):
    t = html.unescape(title.strip())
    # Remove episode/part/season numbers at end
    t = re.sub(r'\s+\d+\s*$', '', t)
    # Remove season/episode markers
    t = re.sub(r'\s+(?:Season|Volume|Vol|Chapter|Episode|Ep|Eп)\s*\d+.*$', '', t, flags=re.I)
    # Remove "Series" suffix
    t = re.sub(r'\s+Series\s*\d*$', '', t, flags=re.I)
    # Remove year at end
    t = re.sub(r'\s+(?:19\d\d|20\d\d)$', '', t)
    # Strip and clean
    t = t.strip()
    return t if t else title

found = 0
for idx, item in remaining:
    title = clean_harder(item['title'])
    year = item.get('year', '')
    
    params = {'api_key': TMDB_KEY, 'query': title, 'language': 'en-US', 'include_adult': True}
    
    for endpoint in ['search/multi', 'search/movie', 'search/tv']:
        try:
            r = requests.get(f'https://api.themoviedb.org/3/{endpoint}', params=params, timeout=10)
            if r.status_code == 200:
                results = r.json().get('results', [])
                if results:
                    poster = results[0].get('poster_path')
                    if poster:
                        data[idx]['poster'] = f'https://image.tmdb.org/t/p/w500{poster}'
                        found += 1
                        print('  FOUND: %s -> %s' % (item['title'][:30], results[0].get('title','')[:30]))
                        break
        except:
            pass
    time.sleep(0.1)

print('\nSecond pass: found=%d, remaining=%d' % (found, len(remaining)-found))

json_str = json.dumps(data, ensure_ascii=False)
with open('data.js', 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('Saved')
