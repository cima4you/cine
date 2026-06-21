import json, re, requests, concurrent.futures, html

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

headers = {'User-Agent': 'Mozilla/5.0'}

# Movies found in sitemap that need poster fetch
sitemap_matches = {
    'Ooyukiumi no Kaina Hoshi no Kenja': 'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-ooyukiumi-no-k',
    'Ultraman Rising': 'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-ultraman-risin',
    'Spy x Family Code White': 'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-spy-x-family-c',
    'Gracie and Pedro Pets to the Rescue': 'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-gracie-and-ped',
    'An Almost Christmas Story': 'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-an-almost-chri',
    'The Bad Guys Haunted Heist': 'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-the-bad-guys-h',
    'Johnny Puff: Secret Mission': 'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-johnny-puff-se',
    'Transformers One': 'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-transformers-o',
}

def norm(t):
    t = t.lower().strip()
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t

# Find indices in data.js
to_fetch = []
for title, url in sitemap_matches.items():
    tn = norm(title)
    for idx, item in enumerate(d):
        if item.get('type') in ('أنمي', 'انمي') and norm(item.get('title','')) == tn:
            to_fetch.append({'idx': idx, 'title': title, 'url': url})
            break

print('Movies to fetch posters for: {}'.format(len(to_fetch)))

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

results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    futures = [ex.submit(fetch_poster, m) for m in to_fetch]
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
            print('  UPDATE: "{}" -> {}'.format(d[idx].get('title','')[:50], new[:70]))
            updated += 1

if updated > 0:
    prefix = content[:content.index('[')]
    suffix = content[content.rindex(']') + 1:]
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(prefix + json.dumps(d, ensure_ascii=False) + suffix)
    print('\nUpdated: {} posters'.format(updated))

# Final stats
anime_final = [x for x in d if x.get('type') in ('أنمي', 'انمي') 
               and str(x.get('year', '')).isdigit() and int(x.get('year', '')) <= 2024]
tuktuk = sum(1 for x in anime_final if 'tuktukhd' in x.get('poster', ''))
print('Final: {}/{} with tuktukhd posters'.format(tuktuk, len(anime_final)))
