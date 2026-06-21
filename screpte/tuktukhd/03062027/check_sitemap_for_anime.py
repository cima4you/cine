import json, re, html

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

# Non-tuktukhd anime
anime = [(i, x) for i, x in enumerate(d) if x.get('type') in ('أنمي', 'انمي') 
         and str(x.get('year', '')).isdigit() and int(x.get('year', '')) <= 2024
         and not x.get('poster', '').startswith('https://tuktukhd')
         and x.get('poster', '')]

print('Still non-tuktukhd: {}'.format(len(anime)))

# Load sitemap
with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'r', encoding='utf-8') as f:
    sitemap = json.load(f)

print('Sitemap entries: {}'.format(len(sitemap)))

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

# Check sitemap for each
for idx, item in anime:
    title = html.unescape(item.get('title', '').strip())
    year = str(item.get('year', ''))
    
    # Check sitemap
    tn = norm(title)
    found = []
    for s in sitemap:
        if s['year'] == year and norm(s['name']) == tn:
            found.append(s)
    
    if found:
        print('Found in sitemap: "{}" ({}) -> {}'.format(title[:50], year, found[0]['url'][:60]))
    else:
        # Try without Arabic prefix
        title_clean = re.sub(r'^فيلم\s+', '', title)
        title_clean = re.sub(r'\s+مدبلج(?:\s+اون\s+لاين)?$', '', title_clean)
        title_clean = re.sub(r'\s+مترجم(?:\s+اون\s+لاين)?$', '', title_clean)
        if title_clean != title:
            tn2 = norm(title_clean)
            for s in sitemap:
                if s['year'] == year and norm(s['name']) == tn2:
                    found.append(s)
            if found:
                print('Found (cleaned) in sitemap: "{}" ({}) -> {}'.format(title[:50], year, found[0]['url'][:60]))
            else:
                print('NOT in sitemap: "{}" ({})'.format(title[:50], year))
        else:
            print('NOT in sitemap: "{}" ({})'.format(title[:50], year))
