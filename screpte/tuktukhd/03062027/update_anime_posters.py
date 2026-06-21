import json, re, requests, concurrent.futures

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

# Anime movies needing poster update
anime = [(i, x) for i, x in enumerate(d) if x.get('type') in ('أنمي', 'انمي') 
         and str(x.get('year', '')).isdigit() and int(x.get('year', '')) <= 2024
         and not x.get('poster', '').startswith('https://tuktukhd')
         and x.get('poster', '')]

print('Anime 2024- needing poster update: {}'.format(len(anime)))

# Load anime results from tuktukhd (has poster URLs)
with open('scripts/tuktukhd/data/results_anime.json', 'r', encoding='utf-8') as f:
    anime_results = json.load(f)

print('Tuktukhd anime results: {}'.format(len(anime_results)))

# Build lookup from tuktukhd results by title+year
def norm(t):
    t = t.lower().strip()
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t

def super_norm(t):
    t = t.lower().strip()
    t = t.replace('ü','u').replace('ğ','g').replace('ş','s').replace('ı','i').replace('ö','o').replace('ç','c')
    t = re.sub(r"\s+\d{4}$", '', t)
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t.strip()

# Build lookup from titre field
results_lookup = {}
for item in anime_results:
    titre = item.get('titre', '')
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم', titre)
    if m:
        name = m.group(1).strip()
        year = m.group(2)
        key = (norm(name), year)
        if key not in results_lookup:
            results_lookup[key] = item['image']

# Also load the anime index for URL matching
with open('scripts/tuktukhd/data/tuktuk_anime_index_v3.json', 'r', encoding='utf-8') as f:
    anime_index = json.load(f)

index_lookup = {}
for item in anime_index:
    key = (norm(item['name']), item['year'])
    if key not in index_lookup:
        index_lookup[key] = item['url']

# Also load sitemap for wider matching
with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'r', encoding='utf-8') as f:
    sitemap = json.load(f)

for item in sitemap:
    key = (norm(item['name']), item['year'])
    if key not in index_lookup:
        index_lookup[key] = item['url']

from difflib import SequenceMatcher

def find_match(title, year):
    key = (norm(title), year)
    # Exact match
    if key in results_lookup:
        return results_lookup[key], 'exact_results'
    if key in index_lookup:
        url = index_lookup[key]
        return None, 'needs_fetch:{}'.format(url)
    
    # Fuzzy match against results
    sn = super_norm(title)
    best = None
    best_score = 0
    for item in anime_results:
        m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم', item.get('titre',''))
        if m:
            r_name = m.group(1).strip()
            r_year = m.group(2)
            yr_diff = abs(int(r_year) - int(year)) if r_year.isdigit() and year.isdigit() else 99
            if yr_diff > 1:
                continue
            r_sn = super_norm(r_name)
            score = SequenceMatcher(None, sn, r_sn).ratio()
            short, long_ = (sn, r_sn) if len(sn) <= len(r_sn) else (r_sn, sn)
            if len(short) >= 5 and short in long_:
                score = max(score, 0.85)
            if score > best_score and score > 0.7:
                best_score = score
                best = item['image']
    
    if best:
        return best, 'fuzzy_results'
    
    # Fuzzy match against index
    for item in anime_index:
        yr_diff = abs(int(item['year']) - int(year)) if item['year'].isdigit() and year.isdigit() else 99
        if yr_diff > 1:
            continue
        i_sn = super_norm(item['name'])
        score = SequenceMatcher(None, sn, i_sn).ratio()
        short, long_ = (sn, i_sn) if len(sn) <= len(i_sn) else (i_sn, sn)
        if len(short) >= 5 and short in long_:
            score = max(score, 0.85)
        if score > best_score and score > 0.7:
            best_score = score
            best = ('needs_fetch:{}'.format(item['url']), 'fuzzy_index')
    
    return best, 'not_found'

# Try to match
matched = []
needs_fetch = []
not_found = []

for idx, item in anime:
    title = item.get('title', '').strip()
    year = str(item.get('year', ''))
    result, method = find_match(title, year)
    
    if result and result.startswith('https://'):
        matched.append({'idx': idx, 'title': title, 'poster': result, 'method': method})
    elif result and result.startswith('needs_fetch:'):
        url = result.split(':', 1)[1]
        needs_fetch.append({'idx': idx, 'title': title, 'year': year, 'url': url, 'method': method})
    else:
        not_found.append({'idx': idx, 'title': title, 'year': year})

print('\nMatched from results: {}'.format(len(matched)))
print('Needs URL fetch: {}'.format(len(needs_fetch)))
print('Not found: {}'.format(len(not_found)))

# Fetch posters for needs_fetch
headers = {'User-Agent': 'Mozilla/5.0'}
def fetch_poster(m):
    try:
        r = requests.get(m['url'], timeout=15, headers=headers)
        pm = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', r.text)
        if pm:
            return {'idx': m['idx'], 'poster': pm.group(1), 'success': True}
        pm = re.search(r'class="[^"]*poster[^"]*"[^>]*src="([^"]+)"', r.text)
        if pm:
            return {'idx': m['idx'], 'poster': pm.group(1), 'success': True}
        return {'idx': m['idx'], 'success': False}
    except:
        return {'idx': m['idx'], 'success': False}

if needs_fetch:
    print('\nFetching {} poster URLs...'.format(len(needs_fetch)))
    fetch_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(fetch_poster, m) for m in needs_fetch]
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            fetch_results.append(future.result())
            if (i + 1) % 20 == 0 or i + 1 == len(needs_fetch):
                print('  {}/{}'.format(i + 1, len(needs_fetch)))
    
    for r in fetch_results:
        if r.get('success'):
            matched.append({'idx': r['idx'], 'title': '', 'poster': r['poster'], 'method': 'fetched'})

print('\nTotal matched (including fetched): {}'.format(len(matched)))

# Update data.js
updated = 0
for m in matched:
    idx = m['idx']
    old = d[idx].get('poster', '')
    new = m['poster']
    if old != new:
        d[idx]['poster'] = new
        if m.get('title'):
            print('  UPDATE: "{}"'.format(m['title'][:50]))
        updated += 1

print('\nPosters updated: {}'.format(updated))

if updated > 0:
    prefix = content[:content.index('[')]
    suffix = content[content.rindex(']') + 1:]
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(prefix + json.dumps(d, ensure_ascii=False) + suffix)
    print('Saved data.js')

# Final stats
anime_final = [x for x in d if x.get('type') in ('أنمي', 'انمي') 
               and str(x.get('year', '')).isdigit() and int(x.get('year', '')) <= 2024]
tuktuk_final = sum(1 for x in anime_final if 'tuktukhd' in x.get('poster', ''))
print('\nFinal: {}/{} anime (2024-) with tuktukhd posters'.format(tuktuk_final, len(anime_final)))

if not_found:
    print('\nStill not found ({}):'.format(len(not_found)))
    for m in not_found[:10]:
        print('  "{}" ({})'.format(m['title'][:50], m['year']))
    if len(not_found) > 10:
        print('  ... and {} more'.format(len(not_found) - 10))
