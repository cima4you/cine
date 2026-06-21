import json, sys, requests, html, re, time
sys.stdout.reconfigure(encoding='utf-8')

API_KEY = 'dac33e2a'
DATA_JS = 'data.js'

with open(DATA_JS, 'r', encoding='utf-8') as f:
    c = f.read()
arr_start = c.index('[')
arr_end = c.rindex(']') + 1
data = json.loads(c[arr_start:arr_end])
prefix = c[:arr_start]
suffix = c[arr_end:]

missing = [(i, x) for i, x in enumerate(data) if x.get('type') == 'أجنبي' and 'tmdb' not in x.get('poster', '').lower() and 'm.media-amazon' not in x.get('poster', '').lower()]
print(f'Still missing: {len(missing)}')

# Manual title corrections for known issues
CORRECTIONS = {
    'KTaken at a Basketball Game': 'Taken at a Basketball Game',
    '!': None,
    'Topâzu': 'Topazu',
    'Mantcora': 'Manticora',
    'Racionais MCs From the Streets of So Paulo': 'Racionais MCs From the Streets of São Paulo',
    'THE HUNTING OPEATIONS': 'The Hunting Operations',
    'Mummy Resurgance': 'Mummy Resurgence',
    'THG The Ballad of Songbirds and Snakes': 'The Hunger Games The Ballad of Songbirds and Snakes',
    'Cdigo Emperador': 'Código Emperador',
    'Peopekteu maen': 'Project Man',
    'A Quiet Place 3 Day One': 'A Quiet Place Day One',
    'Three Flavours Cornetto': 'Three Flavours Cornetto Trilogy',
    'Kill Them Softly': 'Killing Them Softly',  # actual title is "Killing Them Softly"
    'OtaGal 9': 'Ota Gal 9',
    'Orejihanki 10': 'Orejihanki',  # Korean show
}

def gen_titles(raw):
    titles = [raw]
    t = html.unescape(raw.strip())
    
    # Remove year
    m = re.search(r'\s+(19\d\d|20\d\d)$', t)
    year = m.group(1) if m else None
    if year:
        t2 = t[:m.start()].strip()
    else:
        t2 = t
    
    # Manual correction
    if t2 in CORRECTIONS:
        c = CORRECTIONS[t2]
        if c is None:
            return []
        titles.append(c)
    
    # Remove trailing episode markers
    t3 = re.sub(r'\s+(?:Part|Volume|Vol|Chapter|Episode|Webisode)\s+\d+.*$', '', t2, flags=re.I)
    if t3 != t2:
        titles.append(t3)
    
    t4 = re.sub(r'\s+\d+\s*$', '', t2)
    if t4 != t2 and t4 != t3:
        titles.append(t4)
    
    # Remove "Telefilm" suffix
    t5 = re.sub(r'\s+Telefilm$', '', t2, flags=re.I)
    if t5 != t2:
        titles.append(t5)
    
    # Handle specific patterns
    if t2.startswith('Jae seok'):
        titles.append('Jae seok B and B Rules')
    
    if 'Summer of 36' in t2:
        titles.append('Summer of 36')
    
    return list(dict.fromkeys(titles))  # dedupe preserving order

def try_search(title, year):
    params = {'apikey': API_KEY, 't': title, 'plot': 'short'}
    if year:
        params['y'] = year
    try:
        r = requests.get('https://www.omdbapi.com/', params=params, timeout=10)
        if r.status_code == 200:
            j = r.json()
            if j.get('Response') == 'True' and j.get('Poster') and j['Poster'] != 'N/A':
                return j['Poster']
    except:
        pass
    return None

found = 0
not_found = 0
for i, x in missing:
    raw = x['title'].strip()
    m = re.search(r'\s+(19\d\d|20\d\d)$', raw)
    year = m.group(1) if m else None
    
    variants = gen_titles(raw)
    url = None
    for v in variants:
        url = try_search(v, year)
        if url:
            break
        # Also try without year for each variant
        if year:
            url = try_search(v, None)
            if url:
                break
    
    if url:
        data[i]['poster'] = url
        found += 1
        print(f'  OK: {x["title"]} -> {url[:60]}')
    else:
        not_found += 1
    
    if (found + not_found) % 20 == 0:
        print(f'  Progress: {found+not_found}/{len(missing)}: found={found}')
    time.sleep(0.2)

print(f'\nFinal OMDb pass: found={found}, still missing={not_found}')

json_str = json.dumps(data, ensure_ascii=False)
with open(DATA_JS, 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('Saved.')
