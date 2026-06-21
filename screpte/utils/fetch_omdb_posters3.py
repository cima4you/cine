import json, sys, requests, html, re, time, unicodedata
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

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if unicodedata.category(c) != 'Mn')

CORRECTIONS = {
    'Látex rojo': ['Latex rojo', 'Latex Rojo', 'Rojo latex'],
    'Topâzu': ['Topazu', 'Topaz'],
    'Mantcora': ['Manticora', 'Mantícora'],
    'Racionais MCs From the Streets of So Paulo': ['Racionais MCs From the Streets of São Paulo', 'Racionais', 'Racionais MCs'],
    'Cdigo Emperador': ['Codigo Emperador', 'Código Emperador'],
    'Peopekteu maen': ['Project Man', 'Peopekteu maen 2019'],
    'THE HUNTING OPEATIONS': ['The Hunting Operations'],
    'Mummy Resurgance': ['Mummy Resurgence'],
    'THG The Ballad of Songbirds and Snakes': ['The Hunger Games The Ballad of Songbirds and Snakes'],
    'A Thousand Kilometers from Christmas': ['Mil kilometros desde la Navidad', '1000 Kilometers from Christmas'],
    'Things Heard And Seen': ['Things Heard and Seen', 'Things Heard And Seen'],
    'Tin and Tina': ['Tin and Tina', 'Tin & Tina'],
    'Three Flavours Cornetto': ['Three Flavours Cornetto Trilogy', 'Three Flavours Cornetto 1'],
    'The Baztan Trilogy': ['Baztan Trilogy', 'The Baztan Trilogy'],
    'Cem Karacanin Gzyaslari': ['Cem Karacanin Gozyaslari', 'Cem Karacanın Gözyaşları'],
    'Ouija The Awakening': ['Ouija The Awakening', 'Ouija The Awakening 2017', 'Ouija Seance The Final Game'],
    'The Final Load': ['The Final Load 2025', 'Final Load'],
    'DSP Bhullar': ['DSP Bhullar', 'DSP Bhullar 2025'],
    'Cuttputli': ['Cuttputlli', 'Cuttputli'],
    'Sniper G R I T Global Response and Intelligence Team': ['Sniper GRIT', 'Sniper G.R.I.T.'],
    'Rise of the Footsoldier 6 Vengeance': ['Rise of the Footsoldier Vengeance', 'Rise of the Footsoldier 6'],
}

def gen_variants(raw):
    t = html.unescape(raw.strip())
    
    # Strip accents version
    no_acc = strip_accents(t)
    
    # Remove year
    m = re.search(r'\s+(19\d\d|20\d\d)$', t)
    year = m.group(1) if m else None
    base = t[:m.start()].strip() if m else t
    
    # Remove trailing " 1", " 2" etc (episode markers)
    base_noep = re.sub(r'\s+\d+\s*$', '', base)
    base_novol = re.sub(r'\s+(?:Part|Volume|Vol|Chapter|Episode|Webisode)\s+\d+.*$', '', base, flags=re.I)
    
    variants = set()
    for v in [t, base, base_noep, base_novol, no_acc]:
        v = v.strip()
        if v and len(v) >= 2:
            variants.add(v)
    
    # Manual corrections
    for key, vals in CORRECTIONS.items():
        if key in t or key in base:
            for val in vals:
                variants.add(val)
    
    # Replace & with 'and' for search
    for v in list(variants):
        if ' and ' in v:
            variants.add(v.replace(' and ', ' & '))
        if ' & ' in v:
            variants.add(v.replace(' & ', ' and '))
    
    return list(variants), year

def try_omdb(title, year):
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
    variants, year = gen_variants(x['title'])
    url = None
    for v in variants:
        url = try_omdb(v, year)
        if url:
            break
        if year:
            url = try_omdb(v, None)
            if url:
                break
    
    if url:
        data[i]['poster'] = url
        found += 1
        print(f'  OK: {x["title"]}')
    else:
        not_found += 1
    
    if (found + not_found) % 10 == 0:
        print(f'  {found+not_found}/{len(missing)}: found={found}')
    time.sleep(0.25)

print(f'\nFinal pass: found={found}, still missing={not_found}')

json_str = json.dumps(data, ensure_ascii=False)
with open(DATA_JS, 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('Saved.')
