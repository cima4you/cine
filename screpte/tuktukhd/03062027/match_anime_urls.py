import json, re, html

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

anime = [(i, x) for i, x in enumerate(d) if x.get('type') in ('أنمي', 'انمي') 
         and str(x.get('year', '')).isdigit() and int(x.get('year', '')) <= 2023
         and 'tuktukhd' in x.get('poster', '')]

print('Anime 2023- with tuktukhd poster: {}'.format(len(anime)))

# Load index files
indexes = []
for fn in ['scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'scripts/tuktukhd/data/tuktuk_anime_index_v3.json']:
    with open(fn, 'r', encoding='utf-8') as f:
        indexes.extend(json.load(f))

print('Total index entries: {}'.format(len(indexes)))

def norm(t):
    t = t.lower().strip()
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t

matched = []
not_found = []

for idx, item in anime:
    title = html.unescape(item.get('title', '').strip())
    year = str(item.get('year', ''))
    tn = norm(title)
    found = False
    for s in indexes:
        if s['year'] == year and norm(s['name']) == tn:
            matched.append({'idx': idx, 'title': title, 'year': year, 'url': s['url']})
            found = True
            break
    if not found:
        not_found.append({'idx': idx, 'title': title, 'year': year})

print('\nFound in index: {}'.format(len(matched)))
print('Not found in index: {}'.format(len(not_found)))

if matched:
    print('\nSample matches:')
    for m in matched[:5]:
        print('  "{}" ({}) -> {}'.format(m['title'][:40], m['year'], m['url'][:60]))
if not_found:
    print('\nSample not found:')
    for m in not_found[:10]:
        print('  "{}" ({})'.format(m['title'][:50], m['year']))
