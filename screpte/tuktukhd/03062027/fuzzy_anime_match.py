import json, re, html

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

anime = [(i, x) for i, x in enumerate(d) if x.get('type') in ('أنمي', 'انمي') 
         and str(x.get('year', '')).isdigit() and int(x.get('year', '')) <= 2023
         and 'tuktukhd' in x.get('poster', '')]

# Load indexes
indexes = []
for fn in ['scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'scripts/tuktukhd/data/tuktuk_anime_index_v3.json']:
    with open(fn, 'r', encoding='utf-8') as f:
        indexes.extend(json.load(f))

def super_norm(t):
    t = t.lower().strip()
    t = t.replace('ü','u').replace('ğ','g').replace('ş','s').replace('ı','i').replace('ö','o').replace('ç','c')
    t = re.sub(r"\s+\d{4}$", '', t)
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t.strip()

from difflib import SequenceMatcher

# Try fuzzy for not-found
not_found = []
for idx, item in anime:
    title = html.unescape(item.get('title', '').strip())
    year = str(item.get('year', ''))
    tn = super_norm(title)
    found = False
    for s in indexes:
        if s['year'] == year and super_norm(s['name']) == tn:
            found = True
            break
    if not found:
        not_found.append({'idx': idx, 'title': title, 'year': year})

print('Not found (exact): {}'.format(len(not_found)))

# Try fuzzy for first 50
count = 0
for m in not_found[:50]:
    title = m['title']
    year = m['year']
    tn = super_norm(title)
    best = None
    best_score = 0
    for s in indexes:
        yr_diff = abs(int(s['year']) - int(year)) if s['year'].isdigit() and year.isdigit() else 99
        if yr_diff > 1:
            continue
        s_sn = super_norm(s['name'])
        score = SequenceMatcher(None, tn, s_sn).ratio()
        if score > best_score:
            best_score = score
            best = s
    if best and best_score > 0.6:
        print('  "{}" ({}) -> best: "{}" ({}) score={:.2f} {}'.format(
            title[:45], year, best['name'][:45], best['year'], best_score, best['url'][:60] if best_score > 0.75 else ''))
        count += 1

print('\nTotal with fuzzy >0.6: {}'.format(count))
