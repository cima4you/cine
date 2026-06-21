import requests, re, json, concurrent.futures
from difflib import SequenceMatcher

headers = {'User-Agent': 'Mozilla/5.0'}

# Load data.js
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

# Load tuktukhd indexes
with open('scripts/tuktukhd/data/tuktuk_asian_index.json', 'r', encoding='utf-8') as f:
    asian_index = json.load(f)
with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'r', encoding='utf-8') as f:
    sitemap = json.load(f)

combined = asian_index + sitemap

def super_norm(t):
    t = t.lower().strip()
    t = t.replace('ü','u').replace('ğ','g').replace('ş','s').replace('ı','i').replace('ö','o').replace('ç','c')
    t = re.sub(r"\s+\d{4}$", '', t)
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t.strip()

def norm(t):
    t = t.lower().strip()
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t

# Find Asian movies and match to tuktukhd
asian_movies = [(i, x) for i, x in enumerate(d) if x.get('type') == 'أسيوي']
print('Asian movies in data.js: {}'.format(len(asian_movies)))

# Match each to tuktukhd
updates = []
for idx, item in asian_movies:
    title = item.get('title', '').strip()
    year = str(item.get('year', ''))
    current_poster = item.get('poster', '')
    
    # Skip if no current poster (nothing to update)
    if not current_poster:
        # Still try to find poster
        pass
    
    best = None
    best_score = 0
    tn = norm(title)
    
    # Try exact match first
    for s in combined:
        if s['year'] == year and norm(s['name']) == tn:
            best = s
            best_score = 1.0
            break
    
    # Fuzzy match
    if not best:
        sn = super_norm(title)
        for s in combined:
            if s['year'] != year:
                yr_diff = abs(int(s['year']) - int(year)) if s['year'].isdigit() and year.isdigit() else 99
                if yr_diff > 1:
                    continue
            s_sn = super_norm(s['name'])
            score = SequenceMatcher(None, sn, s_sn).ratio()
            short, long_ = (sn, s_sn) if len(sn) <= len(s_sn) else (s_sn, sn)
            if len(short) >= 5 and short in long_:
                score = 0.8 + len(short) / max(len(sn), len(s_sn)) * 0.2
            if score > best_score and score > 0.65:
                best_score = score
                best = s
    
    if best:
        updates.append({'idx': idx, 'title': title, 'year': year, 'url': best['url'], 'score': best_score})

print('Matched to tuktukhd: {}'.format(len(updates)))

if not updates:
    exit()

# Visit pages and extract poster
def extract_poster(u):
    try:
        r = requests.get(u['url'], timeout=15, headers=headers)
        # Try og:image first
        pm = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', r.text)
        if pm:
            return {'idx': u['idx'], 'poster': pm.group(1), 'success': True}
        # Try poster class
        pm = re.search(r'class="[^"]*poster[^"]*"[^>]*src="([^"]+)"', r.text)
        if pm:
            return {'idx': u['idx'], 'poster': pm.group(1), 'success': True}
        return {'idx': u['idx'], 'success': False}
    except:
        return {'idx': u['idx'], 'success': False}

print('Fetching posters from {} pages...'.format(len(updates)))
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
    futures = [ex.submit(extract_poster, u) for u in updates]
    for i, future in enumerate(concurrent.futures.as_completed(futures)):
        results.append(future.result())
        if (i + 1) % 50 == 0 or i + 1 == len(updates):
            print('  {}/{}'.format(i + 1, len(updates)))

successful = [r for r in results if r.get('success')]
print('Posters fetched: {}'.format(len(successful)))

# Update data.js
updated = 0
for r in successful:
    idx = r['idx']
    old_poster = d[idx].get('poster', '')
    new_poster = r['poster']
    # Only update if poster changed
    if old_poster != new_poster:
        d[idx]['poster'] = new_poster
        updated += 1

print('Posters updated: {}'.format(updated))

if updated > 0:
    prefix = content[:content.index('[')]
    suffix = content[content.rindex(']') + 1:]
    json_str = json.dumps(d, ensure_ascii=False)
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(prefix + json_str + suffix)
    print('Saved data.js')
