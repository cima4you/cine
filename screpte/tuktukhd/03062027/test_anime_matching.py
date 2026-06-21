import json, re, html

with open('scripts/tuktukhd/data/results_anime.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

# Titles to search
titles = [
    'باكي هانما ضد كينغان اشورا',
    'المحقق كونان 26 الغواصة الحديدية السوداء',
    'Ooyukiumi no Kaina Hoshi no Kenja',
    'Hello World',
    'Detective Conan Movie 26',
    'Mirai no Mirai',
    'Gold Kingdom and Water Kingdom',
    'World Before You End 2021',
    'Mary and the Witch Flower',
    'Akira',
]

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

# Build results list
result_entries = []
for item in results:
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم', item.get('titre',''))
    if m:
        result_entries.append({'name': m.group(1).strip(), 'year': m.group(2), 'poster': item['image']})

from difflib import SequenceMatcher

for search in titles:
    print('Searching: "{}"'.format(search))
    sn = super_norm(search)
    best = None
    best_score = 0
    for r in result_entries:
        r_sn = super_norm(r['name'])
        score = SequenceMatcher(None, sn, r_sn).ratio()
        if score > best_score:
            best_score = score
            best = r
    
    if best:
        print('  Best match: "{}" ({}), score={:.2f}'.format(best['name'], best['year'], best_score))
    else:
        print('  No match found')
    
    # Also search all result titres
    for r in result_entries:
        if search.lower() in r['name'].lower() or r['name'].lower() in search.lower():
            print('  Substring: "{}" ({})'.format(r['name'], r['year']))
