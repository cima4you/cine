import json, re

def norm(t):
    t = re.sub(r'\s+\d{4}$', '', t.lower().strip())
    t = re.sub(r"[`'’‘:.,!?&/\-]", ' ', t)
    t = re.sub(r'\s+', '', t)
    return t.strip()

# Check sitemap
with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'r', encoding='utf-8') as f:
    sitemap = json.load(f)

# Check category listings
with open('scripts/tuktukhd/data/tuktuk_other_categories.json', 'r', encoding='utf-8') as f:
    cats = json.load(f)

# Combined lookup
combined = sitemap + cats

remaining = [
    ('Merakli Adamin 10 Günü', '2024', 'تركي'),
    ('Sarah Silverman: PostMortem 2025', '2025', 'نتفليكس'),
    ('Kakegurui 2', '2024', 'أسيوي'),
    ('My Hero Academia: You\'re Next', '2024', 'أنمي'),
    ('Blue Cave', '2024', 'تركي'),
    ('Kül', '2024', 'تركي'),
    ('Love Tactics', '2022', 'تركي'),
    ('Love Tactics 2', '2023', 'تركي'),
    ('The Rose of Versailles', '2025', 'نتفليكس'),
    ('Hesitation Wound', '2023', 'تركي'),
    ('Death Before the Wedding', '2025', 'أجنبي'),
    ('Chelsea Handler: The Feeling', '2025', 'وثائقي'),
    ('Rüzgara Birak 2025', '2025', 'نتفليكس'),
    ('Malazgirt 1071 2022', '2022', 'نتفليكس'),
    ('سيكو سيكو', '2025', 'عربي'),
    ('The Funeral', '2023', 'تركي'),
    ('Romantik Hirsiz', '2024', 'تركي'),
    ('Türkler Geliyor: Adaletin Kilici', '2022', 'تركي'),
    ('Cadı', '2024', 'تركي'),
    ('2 Sailor Moon Cosmos Part', '2023', 'أنمي'),
    ('Seishun buta yaro wa ransel girl no yume o minai', '2023', 'أنمي'),
    ('Touken Ranbu Kai Douden Chikashi Haberau Monora', '2024', 'أنمي'),
    ('The Feast of Amrita', '2023', 'أنمي'),
    ('Mononoke Paper Umbrella', '2024', 'أنمي'),
    ('Ai-naki mori de sakebe', '2019', 'نتفليكس'),
    ('Haikyū!! La Guerre des poubelles', '2024', 'أنمي'),
]

from difflib import SequenceMatcher

def sim(a, b):
    return SequenceMatcher(None, norm(a), norm(b)).ratio()

print('Searching combined index ({}+{}={} entries)...'.format(len(sitemap), len(cats), len(combined)))
print()

for title, year, typ in remaining:
    tn = norm(title)
    best = None
    best_score = 0
    best_year = ''
    for m in combined:
        mn = norm(m['name'])
        yr_diff = abs(int(m['year']) - int(year)) if m['year'].isdigit() and year.isdigit() else 999
        if yr_diff > 1:
            continue
        score = sim(title, m['name'])
        if score > best_score:
            best_score = score
            best = m['name']
            best_year = m['year']
    
    if best_score > 0.5:
        print('  "{}" ({}) [{}] -> BEST: "{}" ({}) score={:.2f}'.format(title, year, typ, best, best_year, best_score))
    else:
        print('  "{}" ({}) [{}] -> NO MATCH (best={:.2f})'.format(title, year, typ, best_score))
