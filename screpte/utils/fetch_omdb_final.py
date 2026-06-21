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

# Very precise manual title corrections
HARDCODED = {
    'Harry Potter 1 and the Sorcerer\u2019s Stone 2001': 'Harry Potter and the Sorcerer\u2019s Stone',
    'Harry Potter 1 and the Sorcerer&#8217;s Stone 2001': 'Harry Potter and the Sorcerer\u2019s Stone',
    "To All the Boys 1 I've Loved Before 2018": "To All the Boys I've Loved Before",
    'To All the Boys 1 I&#8217;ve Loved Before 2018': "To All the Boys I've Loved Before",
    "Amy\u2019s Fucket List 2023": "Amy's Fucket List",
    'Amy&#8217;s Fucket List 2023': "Amy's Fucket List",
    "Jae seok\u2019s B and B Rules 10": "Jae seok's B and B Rules",
    "Jae seok\u2019s B and B Rules 9": "Jae seok's B and B Rules",
    "Jae seok\u2019s B and B Rules 8": "Jae seok's B and B Rules",
    "Jae seok\u2019s B and B Rules 7": "Jae seok's B and B Rules",
    "Jae seok\u2019s B and B Rules 6": "Jae seok's B and B Rules",
    'Salaar Cease Fire \u2013 Part 1 2023': 'Salaar Cease Fire',
    'Salaar Cease Fire &#8211; Part 1 2023': 'Salaar Cease Fire',
    'Cdigo Emperador 2022': 'Codigo Emperador',
    'Peopekteu maen 2019': 'Project Man',
    'THE HUNTING OPEATIONS 2021': 'The Hunting Operations',
    'Mummy Resurgance 2021': 'Mummy Resurgence',
    'The Final Load 2025': 'Final Load',
    'L\u00e1tex rojo 2020': 'Latex Rojo',
    'Látex rojo 2020': 'Latex Rojo',
    'Guard: Revenge for Love 2025': 'Guard Revenge for Love',
    'Mantcora 2022': 'Mantícora',
    'Cem Karacanin Gzyaslari 2024': 'Cem Karacan',
    'Summer of 36 1': 'Summer of 36',
    'Summer of 36 2': 'Summer of 36',
    'Summer of 36 3': 'Summer of 36',
    'Summer of 36 4': 'Summer of 36',
    'Summer of 36 5': 'Summer of 36',
    'Summer of 36 6': 'Summer of 36',
    'OtaGal 9': 'OtaGal',
    'Orejihanki 10': 'Orejihanki',
    'Three Flavours Cornetto': "Shaun of the Dead",
    'The Baztan Trilogy': 'The Baztan Trilogy',
    'B and B Merry 2022': 'B and B Merry',
    'A Thousand Kilometers from Christmas 2021': 'A Thousand Kilometers from Christmas',
    'White Skin Black Thighs 1976': 'White Skin Black Thighs',
}

found = 0
not_found = 0
for i, x in missing:
    raw = x['title'].strip()
    search_title = raw
    
    # Check hardcoded corrections
    if raw in HARDCODED:
        search_title = HARDCODED[raw]
    else:
        # General cleanup
        st = html.unescape(raw)
        st = re.sub(r'\s+\d+\s*$', '', st)  # remove trailing number
        st = re.sub(r'\s+(?:Volume|Vol|Part|Season)\s+\d+.*$', '', st, flags=re.I)
        # Remove " 1" " 2" etc that were episode markers
        st = re.sub(r'\s+\d+\s+(?:I\s+|\w+\s+)?', ' ', st)
        # Remove year
        st = re.sub(r'\s+(19\d\d|20\d\d)$', '', st)
        search_title = st.strip()
    
    # Extract year from original
    m = re.search(r'(19\d\d|20\d\d)', raw)
    year = m.group(1) if m else None
    
    # Try OMDb
    for t in [search_title, search_title.replace(' and ', ' & '), search_title.replace(' & ', ' and ')]:
        params = {'apikey': API_KEY, 't': t, 'plot': 'short'}
        if year:
            params['y'] = year
        try:
            r = requests.get('https://www.omdbapi.com/', params=params, timeout=10)
            if r.status_code == 200:
                j = r.json()
                if j.get('Response') == 'True' and j.get('Poster') and j['Poster'] != 'N/A':
                    data[i]['poster'] = j['Poster']
                    found += 1
                    print(f'  OK: {x["title"]} -> {t}')
                    break
        except:
            pass
        # Try without year
        if year:
            params.pop('y', None)
            try:
                r = requests.get('https://www.omdbapi.com/', params=params, timeout=10)
                if r.status_code == 200:
                    j = r.json()
                    if j.get('Response') == 'True' and j.get('Poster') and j['Poster'] != 'N/A':
                        data[i]['poster'] = j['Poster']
                        found += 1
                        print(f'  OK: {x["title"]} -> {t}')
                        break
            except:
                pass
    else:
        not_found += 1
    
    if (found + not_found) % 10 == 0:
        print(f'  {found+not_found}/{len(missing)}: found={found}')
    time.sleep(0.3)

print(f'\nFinal hardcoded pass: found={found}, still missing={not_found}')

json_str = json.dumps(data, ensure_ascii=False)
with open(DATA_JS, 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print('Saved.')
