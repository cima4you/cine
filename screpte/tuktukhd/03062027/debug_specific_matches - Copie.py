import json, re

with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'r', encoding='utf-8') as f:
    sitemap = json.load(f)

with open('scripts/tuktukhd/data/tuktuk_other_categories.json', 'r', encoding='utf-8') as f:
    cats = json.load(f)

combined = sitemap + cats

def norm(t):
    t = t.lower().strip()
    t = t.replace('ü', 'u').replace('Ü', 'u')
    t = t.replace('ğ', 'g').replace('Ğ', 'g')
    t = t.replace('ş', 's').replace('Ş', 's')
    t = t.replace('ı', 'i').replace('I', 'i')
    t = t.replace('ö', 'o').replace('Ö', 'o')
    t = t.replace('ç', 'c').replace('Ç', 'c')
    t = t.replace('è', 'e').replace('é', 'e').replace('ê', 'e').replace('ë', 'e')
    t = t.replace('à', 'a').replace('á', 'a').replace('â', 'a').replace('ã', 'a')
    t = t.replace('ì', 'i').replace('í', 'i').replace('î', 'i')
    t = t.replace('ò', 'o').replace('ó', 'o').replace('ô', 'o').replace('õ', 'o')
    t = t.replace('ù', 'u').replace('ú', 'u').replace('û', 'u')
    t = re.sub(r"[`'’‘:.,!?&/\-]", ' ', t)
    t = re.sub(r'\s+', '', t)
    return t.strip()

from difflib import SequenceMatcher

targets = [
    ('My Hero Academia: You\'re Next', '2024'),
    ('Blue Cave', '2024'),
    ('Kakegurui 2', '2024'),
    ('Haikyū!! La Guerre des poubelles', '2024'),
    ('2 Sailor Moon Cosmos Part', '2023'),
    ('Mononoke Paper Umbrella', '2024'),
    ('The Rose of Versailles', '2025'),
]

for t_title, t_year in targets:
    tn = norm(t_title)
    print('\n"{}" ({}) [norm="{}"]'.format(t_title, t_year, tn))
    best = None
    best_score = 0
    for s in combined:
        sn = norm(s['name'])
        yr_diff = abs(int(s['year']) - int(t_year)) if s['year'].isdigit() and t_year.isdigit() else 999
        if yr_diff > 1:
            continue
        score = SequenceMatcher(None, tn, sn).ratio()
        short, long_ = (tn, sn) if len(tn) <= len(sn) else (sn, tn)
        if len(short) >= 5 and short in long_:
            score = 0.85 + len(short) / max(len(tn), len(sn)) * 0.15
        if score > best_score:
            best_score = score
            best = (s['name'], s['year'], sn, score)
    if best:
        print('  BEST: "{}" ({}) [norm="{}"] score={:.3f}'.format(*best))
