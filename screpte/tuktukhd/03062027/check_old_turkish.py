import json, re, html

with open('scripts/tuktukhd/data/results_turkish_real.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

# Parse names from results
def parse_titre(titre):
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم(?:\s+اون\s+لاين)?', titre)
    if m:
        return m.group(1).strip(), m.group(2)
    return None, None

result_names = set()
for r in results:
    name, year = parse_titre(r.get('titre', ''))
    if name and year:
        result_names.add((name, year))

print('Results entries: {}'.format(len(results)))
print('Unique result names: {}'.format(len(result_names)))

# Now compare with the OLD Turkish movies that were removed
old_turkish_titles = [
    ("39 Derecede Ask", "2024"),
    ("Siccin 7", "2024"),
    ("Merakli Adamin 10 Günü", "2024"),
    ("Blue Cave", "2024"),
    ("A True Gentleman", "2024"),
    ("The Funeral", "2023"),
    ("3391 Kilometre", "2024"),
    ("Lohusa", "2024"),
    ("Romantik Hirsiz", "2024"),
    ("Ölümlü Dünya 2", "2024"),
    ("Kül", "2024"),
    ("Bihter", "2023"),
    ("Erdal ile Ece", "2024"),
    ("Sevda: Mecburi Istikamet", "2023"),
    ("Gelin Takimi", "2024"),
    ("Dengeler", "2024"),
    ("Crossing", "2024"),
    ("Baska Bir Sen", "2025"),
    ("Love Tactics", "2022"),
    ("Love Tactics 2", "2023"),
    ("Malazgirt 1071", "2022"),
    ("Türkler Geliyor: Adaletin Kilici", "2022"),
    ("Cadı", "2024"),
    ("Hesitation Wound", "2023"),
    ("49", "2023"),
    ("Kuru Otlar Ustune", "2023"),
    ("3391 Kilometre", "2023"),
    ("Hayatla Baris", "2024"),
    ("Aşk Mevsimi", "2024"),
    ("Ayla The Daughter of War", "2017"),
    ("Ruyanda Gorursun", "2023"),
    ("Last Call for Istanbul", "2023"),
    ("Oregon", "2023"),
    ("Bandirma Fuze Kulubu", "2022"),
    ("Prestij Meselesi", "2023"),
    ("Uçus 811", "2022"),
    ("Do Not Disturb", "2023"),
    ("Anka", "2022"),
    ("صلاح الدين الأيوبي فاتح القدس", "2023"),
    ("المؤسس عثمان", "2019"),
]

found = 0
not_found = []
for title, year in old_turkish_titles:
    # Normalize
    tn = title.lower().strip()
    tn = re.sub(r"[`'’‘:.,!?&/\-]", '', tn)
    tn = re.sub(r'\s+', '', tn)
    
    key_found = False
    for rn, ry in result_names:
        rnn = rn.lower().strip()
        rnn = re.sub(r"[`'’‘:.,!?&/\-]", '', rnn)
        rnn = re.sub(r'\s+', '', rnn)
        if rnn == tn and ry == year:
            key_found = True
            break
    
    if key_found:
        found += 1
    else:
        not_found.append((title, year))

print('\nFound in new results: {}'.format(found))
print('Not found in new results: {}'.format(len(not_found)))
for t, y in not_found:
    print(f'  "{t}" ({y})')
