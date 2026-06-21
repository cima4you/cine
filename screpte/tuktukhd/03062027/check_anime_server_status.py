import json, re

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

anime = [(i, x) for i, x in enumerate(d) if x.get('type') in ('أنمي', 'انمي') 
         and str(x.get('year', '')).isdigit() and int(x.get('year', '')) <= 2023]

# Count movies with tuktukhd poster (means they exist on tuktukhd)
with_tuk = []
without_tuk = []
for idx, item in anime:
    if 'tuktukhd' in item.get('poster', ''):
        with_tuk.append((idx, item))
    else:
        without_tuk.append((idx, item))

print('Anime 2023- with tuktukhd poster: {}'.format(len(with_tuk)))
print('Anime 2023- WITHOUT tuktukhd poster: {}'.format(len(without_tuk)))

# Check server quality for those with tuktukhd poster
def has_multi_quality(item):
    servers = item.get('servers', [])
    for s in servers if isinstance(servers, list) else []:
        name = s.get('name', '')
        if 'متعدد' in name or 'جودة' in name:
            return True
    return False

tuk_multi = [(i, x) for i, x in with_tuk if has_multi_quality(x)]
tuk_good = [(i, x) for i, x in with_tuk if not has_multi_quality(x) and x.get('servers')]

print('\nWith tuktukhd poster + multi-quality server: {}'.format(len(tuk_multi)))
print('With tuktukhd poster + already good: {}'.format(len(tuk_good)))

# Check what servers the "good" ones use
if tuk_good:
    print('\nSample servers from "good" ones:')
    for idx, item in tuk_good[:3]:
        servers = item.get('servers', [])
        names = [s.get('name','') for s in servers[:4]]
        print('  "{}" ({}) -> {}'.format(item.get('title','').strip()[:40], item.get('year',''), names))

# For ones WITHOUT tuktukhd poster - check if they exist in our anime index/sitemap
print('\n--- WITHOUT tuktukhd poster ---')
for idx, item in without_tuk[:10]:
    print('  "{}" ({}) multi: {} servers: {}'.format(
        item.get('title','').strip()[:40], item.get('year',''),
        has_multi_quality(item),
        [s.get('name','') for s in item.get('servers',[])][:3] if item.get('servers') else 'NO SERVERS'))
