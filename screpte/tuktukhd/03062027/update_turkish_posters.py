import json, re, html

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

# Turkish movies without tuktukhd posters
turkish_old = [(i, x) for i, x in enumerate(d) if x.get('type') == 'تركي'
               and not x.get('poster', '').startswith('https://tuktukhd')]

print('Turkish without tuktukhd poster: {}'.format(len(turkish_old)))

# Load results
with open('scripts/tuktukhd/data/results_turkish.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

print('Results available: {}'.format(len(results)))

def norm(t):
    t = t.lower().strip()
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t

# Build results lookup
def parse_titre(titre):
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم(?:\s+اون\s+لاين)?', titre)
    if m:
        return m.group(1).strip(), m.group(2)
    return None, None

results_by_year = {}
for r in results:
    name, year = parse_titre(r.get('titre', ''))
    if name and year:
        rn = norm(name)
        if year not in results_by_year:
            results_by_year[year] = {}
        results_by_year[year][rn] = r

# Match and update
updated_posters = 0
updated_servers = 0
for idx, item in turkish_old:
    title = html.unescape(item.get('title', '').strip())
    year = str(item.get('year', ''))
    tn = norm(title)
    
    if year in results_by_year and tn in results_by_year[year]:
        r = results_by_year[year][tn]
        old_poster = item.get('poster', '')
        new_poster = r.get('image', '')
        if new_poster and old_poster != new_poster:
            d[idx]['poster'] = new_poster
            updated_posters += 1
            print('  Poster: "{}" ({})'.format(title[:40], year))
        
        # Update servers if multi-quality
        servers = item.get('servers', [])
        if any('متعدد' in s.get('name','') or 'جودة' in s.get('name','') for s in (servers or [])):
            if 'servers' in r and isinstance(r['servers'], dict):
                r_servers = r['servers']
                watch = r_servers.get('watch', [])
                download = r_servers.get('download', [])
                
                new_servers = []
                for ws in watch:
                    new_servers.append({
                        'name': ws.get('name', 'TukTuk Vip'),
                        'url': ws.get('url', ''),
                        'isDefault': ws.get('isDefault', False)
                    })
                for ds in download:
                    if ds.get('url'):
                        new_servers.append({
                            'name': ds.get('name', 'Download'),
                            'url': ds.get('url', ''),
                            'isDefault': False
                        })
                
                if new_servers:
                    # Also preserve additional servers that aren't multi-quality
                    kept = []
                    for s in servers:
                        if not ('متعدد' in s.get('name','') or 'جودة' in s.get('name','')):
                            kept.append(s)
                    d[idx]['servers'] = kept + new_servers
                    updated_servers += 1
                    print('  Servers: "{}" ({})'.format(title[:40], year))

if updated_posters > 0 or updated_servers > 0:
    prefix = content[:content.index('[')]
    suffix = content[content.rindex(']') + 1:]
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(prefix + json.dumps(d, ensure_ascii=False) + suffix)
    print('\nPosters updated: {}, Servers updated: {}'.format(updated_posters, updated_servers))
else:
    print('\nNo updates needed')
