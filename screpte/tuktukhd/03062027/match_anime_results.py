import json, re, html

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

anime = [(i, x) for i, x in enumerate(d) if x.get('type') in ('أنمي', 'انمي') 
         and str(x.get('year', '')).isdigit() and int(x.get('year', '')) <= 2023]

print('Anime 2023- in data.js: {}'.format(len(anime)))

# Load results_anime
with open('scripts/tuktukhd/data/results_anime.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

print('Results_anime entries: {}'.format(len(results)))

def norm(t):
    t = t.lower().strip()
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t

# Extract name+year from titre
results_clean = []
for r in results:
    titre = r.get('titre', '')
    # Parse "فيلم Name YEAR مترجم اون لاين"
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم(?:\s+اون\s+لاين)?', titre)
    if m:
        name = m.group(1).strip()
        year = m.group(2)
        results_clean.append({'name': name, 'year': year, 'servers': r['servers'], 'image': r.get('image','')})

print('Parsed results: {}'.format(len(results_clean)))

# Match
matched = []
not_found = []
for idx, item in anime:
    title = html.unescape(item.get('title', '').strip())
    year = str(item.get('year', ''))
    tn = norm(title)
    found = None
    for r in results_clean:
        if r['year'] == year:
            rn = norm(r['name'])
            if rn == tn:
                found = r
                break
    
    if found:
        matched.append({'idx': idx, 'title': title, 'year': year, 'servers': found['servers'], 'image': found['image']})
    else:
        not_found.append({'idx': idx, 'title': title, 'year': year})

print('\nMatched: {}'.format(len(matched)))
print('Not found: {}'.format(len(not_found)))

if matched:
    print('\nSample matched:')
    for m in matched[:5]:
        print('  "{}" ({})'.format(m['title'][:40], m['year']))
if not_found:
    print('\nSample not found:')
    for m in not_found[:10]:
        print('  "{}" ({})'.format(m['title'][:50], m['year']))
