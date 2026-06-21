import json, re, requests, concurrent.futures, html

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

# Still non-tuktukhd anime 2024-
anime = [(i, x) for i, x in enumerate(d) if x.get('type') in ('أنمي', 'انمي') 
         and str(x.get('year', '')).isdigit() and int(x.get('year', '')) <= 2024
         and not x.get('poster', '').startswith('https://tuktukhd')
         and x.get('poster', '')]

print('Still needing poster update: {}'.format(len(anime)))

# Load tuktukhd anime results
with open('scripts/tuktukhd/data/results_anime.json', 'r', encoding='utf-8') as f:
    anime_results = json.load(f)

# Build lookup
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

def clean_arabic_title(t):
    """Strip Arabic prefixes like فيلم, مدبلج, etc."""
    t = re.sub(r'^فيلم\s+', '', t)
    t = re.sub(r'\s+مدبلج(?:\s+اون\s+لاين)?$', '', t)
    t = re.sub(r'\s+مترجم(?:\s+اون\s+لاين)?$', '', t)
    return t.strip()

results_entries = []
for item in anime_results:
    titre = item.get('titre', '')
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم', titre)
    if m:
        name = m.group(1).strip()
        year = m.group(2)
        results_entries.append({'name': name, 'year': year, 'poster': item['image']})

# Also load anime index
with open('scripts/tuktukhd/data/tuktuk_anime_index_v3.json', 'r', encoding='utf-8') as f:
    anime_index = json.load(f)

with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'r', encoding='utf-8') as f:
    sitemap = json.load(f)

all_index = anime_index + sitemap

from difflib import SequenceMatcher

matched = []
not_found = []

for idx, item in anime:
    title_raw = item.get('title', '').strip()
    year = str(item.get('year', ''))
    
    # Clean the title
    title = html.unescape(title_raw)
    title_clean = clean_arabic_title(title)
    
    found = False
    
    # Try 1: exact match with clean title in results
    tn = norm(title_clean)
    for r in results_entries:
        if r['year'] == year and norm(r['name']) == tn:
            matched.append({'idx': idx, 'poster': r['poster'], 'method': 'exact_clean'})
            found = True
            break
    
    if found:
        continue
    
    # Try 2: fuzzy match in results
    sn = super_norm(title_clean)
    best = None
    best_score = 0
    for r in results_entries:
        yr_diff = abs(int(r['year']) - int(year)) if r['year'].isdigit() and year.isdigit() else 99
        if yr_diff > 1:
            continue
        r_sn = super_norm(r['name'])
        score = SequenceMatcher(None, sn, r_sn).ratio()
        short, long_ = (sn, r_sn) if len(sn) <= len(r_sn) else (r_sn, sn)
        if len(short) >= 5 and short in long_:
            score = max(score, 0.85)
        if score > best_score and score > 0.8:
            best_score = score
            best = r['poster']
    
    if best:
        matched.append({'idx': idx, 'poster': best, 'method': 'fuzzy_clean ({:.2f})'.format(best_score)})
        continue
    
    # Try 3: search via TMDb to find English title, then match to tuktukhd
    # Skip complex matching, just mark as not found
    not_found.append({'idx': idx, 'title': title_raw, 'year': year, 'cleaned': title_clean})

print('\nMatched: {}'.format(len(matched)))
print('Not found: {}'.format(len(not_found)))

# Update data.js
updated = 0
for m in matched:
    idx = m['idx']
    old = d[idx].get('poster', '')
    new = m['poster']
    if old != new:
        d[idx]['poster'] = new
        updated += 1
        print('  UPDATE: "{}" ({})'.format(d[idx].get('title','').strip()[:50], m['method']))

if updated > 0:
    prefix = content[:content.index('[')]
    suffix = content[content.rindex(']') + 1:]
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(prefix + json.dumps(d, ensure_ascii=False) + suffix)
    print('\nUpdated: {}'.format(updated))

if not_found:
    print('\nStill not found ({}):'.format(len(not_found)))
    for m in not_found[:10]:
        print('  "{}" ({}) cleaned="{}"'.format(m['title'][:50], m['year'], m['cleaned'][:40]))
