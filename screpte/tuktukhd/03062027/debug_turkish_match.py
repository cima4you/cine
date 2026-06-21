import json, re, html

with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
d = json.loads(content[content.index('['):content.rindex(']')+1])

turkish_old = [(i, x) for i, x in enumerate(d) if x.get('type') == 'تركي'
               and not x.get('poster', '').startswith('https://tuktukhd')]

with open('scripts/tuktukhd/data/results_turkish.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

def norm(t):
    t = t.lower().strip()
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t

def parse_titre(titre):
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم(?:\s+اون\s+لاين)?', titre)
    if m:
        return m.group(1).strip(), m.group(2)
    return None, None

# Show first 10 old turkish and try to find matches
for idx, item in turkish_old[:10]:
    title = html.unescape(item.get('title', '').strip())
    year = str(item.get('year', ''))
    tn = norm(title)
    print('Looking for: "{}" ({}) norm="{}"'.format(title[:50], year, tn[:30]))
    
    # Search results
    found = []
    for r in results:
        name, ry = parse_titre(r.get('titre', ''))
        if name and ry == year:
            rn = norm(name)
            if tn == rn:
                found.append(r)
            elif tn in rn or rn in tn:
                found.append(r)
    
    if found:
        print('  Matched: {}'.format(found[0].get('titre','')[:50]))
    else:
        # Show first few results with same year
        same_yr = []
        for r in results:
            name, ry = parse_titre(r.get('titre', ''))
            if ry == year:
                same_yr.append(norm(name))
        print('  NOT FOUND. Same year examples: {}'.format([x[:30] for x in same_yr[:5]]))
    print()
