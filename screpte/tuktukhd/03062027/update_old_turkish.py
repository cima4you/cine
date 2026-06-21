import json, re, html, requests, concurrent.futures, base64

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

turkish = [(i, x) for i, x in enumerate(d) if x.get('type') == 'تركي'
           and not x.get('poster', '').startswith('https://tuktukhd')]

print('Old Turkish movies needing update: {}'.format(len(turkish)))

# Load sitemap
with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'r', encoding='utf-8') as f:
    sitemap = json.load(f)

# Also load anime index and turkish listing
with open('scripts/tuktukhd/data/tuktuk_anime_index_v3.json', 'r', encoding='utf-8') as f:
    anime_idx = json.load(f)

all_idx = sitemap + anime_idx

# Add the turkish listing we just scraped (urls from listing pages)
with open('scripts/tuktukhd/data/turkish_listing.json', 'r', encoding='utf-8') as f:
    listing = json.load(f)
for m in listing:
    all_idx.append({'name': m['name'], 'year': m['year'], 'url': m['url']})

print('Total index entries: {}'.format(len(all_idx)))

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

from difflib import SequenceMatcher

headers = {'User-Agent': 'Mozilla/5.0'}

matched = []
for idx, item in turkish:
    title = html.unescape(item.get('title', '').strip())
    year = str(item.get('year', ''))
    tn = super_norm(title)
    
    best = None
    best_score = 0
    for s in all_idx:
        yr_diff = abs(int(s['year']) - int(year)) if s['year'].isdigit() and year.isdigit() else 99
        if yr_diff > 1:
            continue
        s_sn = super_norm(s['name'])
        score = SequenceMatcher(None, tn, s_sn).ratio()
        if score > best_score and score > 0.75:
            best_score = score
            best = s
    
    if best:
        matched.append({'idx': idx, 'title': title, 'year': year, 'url': best['url'], 'score': best_score})
        print('  MATCH: "{}" ({}) score={:.2f}'.format(title[:40], year, best_score))
    else:
        print('  NO MATCH: "{}" ({})'.format(title[:40], year))

print('\nTotal matched: {}'.format(len(matched)))
if matched:
    # Fetch posters for matched
    print('\nFetching posters for matched...')
    def fetch_poster(m):
        try:
            r = requests.get(m['url'], timeout=15, headers=headers)
            pm = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', r.text)
            if pm:
                return {'idx': m['idx'], 'poster': pm.group(1), 'success': True}
            return {'idx': m['idx'], 'success': False}
        except:
            return {'idx': m['idx'], 'success': False}
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(fetch_poster, m) for m in matched]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    updated = 0
    for r in results:
        if r.get('success'):
            idx = r['idx']
            old = d[idx].get('poster', '')
            new = r['poster']
            if old != new:
                d[idx]['poster'] = new
                updated += 1
                print('  UPDATE: "{}"'.format(d[idx].get('title','').strip()[:50]))
    
    if updated > 0:
        prefix = content[:content.index('[')]
        suffix = content[content.rindex(']') + 1:]
        with open('data.js', 'w', encoding='utf-8') as f:
            f.write(prefix + json.dumps(d, ensure_ascii=False) + suffix)
        print('\nUpdated: {} posters'.format(updated))
    else:
        print('No posters to update')
