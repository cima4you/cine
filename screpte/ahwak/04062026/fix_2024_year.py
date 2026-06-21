import json, sys
sys.stdout.reconfigure(encoding='utf-8')
with open('scripts/ahwak/data/results_yam_moslslat_ramadan_2024.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for s in data:
    if not s.get('year'):
        s['year'] = '2024'
    cats = s.get('categories', [])
    if not cats:
        s['categories'] = ['مسلسلات رمضان 2024']

with open('scripts/ahwak/data/results_yam_moslslat_ramadan_2024.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('Fixed year for all entries. Total series:', len(data))
