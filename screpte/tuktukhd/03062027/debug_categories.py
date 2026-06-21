import json, re

with open('scripts/tuktukhd/data/tuktuk_other_categories.json', 'r', encoding='utf-8') as f:
    cats = json.load(f)

def norm(t):
    t = re.sub(r'\s+\d{4}$', '', t.lower().strip())
    t = re.sub(r"[`'’‘:.,!?&/\-]", ' ', t)
    t = re.sub(r'\s+', '', t)
    return t.strip()

# Search for each remaining item
test_items = [
    'Merakli Adamin 10 Günü',
    'Sarah Silverman: PostMortem 2025',
    'Kakegurui 2',
    'My Hero Academia: You\'re Next',
    'Blue Cave',
    'Kül',
    'Love Tactics',
    'Love Tactics 2',
    'The Rose of Versailles',
    'Hesitation Wound',
    'Death Before the Wedding',
    'Chelsea Handler: The Feeling',
    'Rüzgara Birak 2025',
    'Malazgirt 1071 2022',
    'Cadı',
    'The Funeral',
    'Romantik Hirsiz',
    'Türkler Geliyor: Adaletin Kilici',
]

for test in test_items:
    tn = norm(test)
    found = False
    for m in cats:
        nn = norm(m['name'])
        if tn == nn:
            print('EXACT: "{}" ({}) -> "{}" ({})'.format(test, '', m['name'], m['year']))
            found = True
            break
        elif len(tn) >= 5 and len(nn) >= 5 and (tn in nn or nn in tn):
            print('SUB: "{}" ({}) -> "{}" ({})'.format(test, '', m['name'], m['year']))
            found = True
            break
    if not found:
        print('NOT FOUND: "{}"'.format(test))

# Also check anime titles
print('\n--- Anime sub-search ---')
anime_items = [
    'Touken Ranbu Kai Douden Chikashi Haberau Monora',
    'The Feast of Amrita',
    'Mononoke Paper Umbrella',
    'Haikyū!! La Guerre des poubelles',
    '2 Sailor Moon Cosmos Part',
    'Seishun buta yaro wa ransel girl no yume o minai',
]
for test in anime_items:
    tn = norm(test)
    found = False
    for m in cats:
        nn = norm(m['name'])
        if len(tn) >= 5 and len(nn) >= 5 and (tn in nn or nn in tn):
            print('MATCH: "{}" -> "{}" ({})'.format(test, m['name'], m['year']))
            found = True
            break
    if not found:
        print('NO MATCH: "{}"'.format(test))
