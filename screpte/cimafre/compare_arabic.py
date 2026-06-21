import re, json

# Read cimafre movies (419 with servers)
cimafre = json.load(open('data/data-cimafre.json', 'r', encoding='utf-8'))
cimafre_titles = set()
for m in cimafre:
    t = m.get('title_clean', '') or m.get('title', '')
    t = re.sub(r'^مشاهدة (فيلم|مسلسل|انمي)\s+', '', t)
    t = re.sub(r'\s+كامل اون لاين.*', '', t)
    cimafre_titles.add(t.strip().lower())

print(f'Cimafre movies: {len(cimafre_titles)} (with servers: {len(cimafre)})')

# Read data-arabic.js (existing Arabic movies)
with open('data/data-arabic.js', 'r', encoding='utf-8') as f:
    js_content = f.read()

# Extract titles from JS array
arabic_titles = set()
for m in re.finditer(r'title:"([^"]*)"', js_content):
    arabic_titles.add(m.group(1).strip().lower())

# Also try to get the full objects
arabic_objects = []
pattern = r'\{[^}]*title:"([^"]*)"[^}]*type:"عربي"[^}]*\}'
for m in re.finditer(pattern, js_content, re.DOTALL):
    t = m.group(1).strip()
    arabic_objects.append(t)

print(f'Arabic.js movies: {len(arabic_titles)}')
print(f'Arabic.js (with type:عربي): {len(arabic_objects)}')

# Find movies in arabic.js but not in cimafre
missing = arabic_titles - cimafre_titles
print(f'\n== Arabic movies NOT in cimafre: {len(missing)} ==')
for t in sorted(missing)[:50]:
    print(t)
if len(missing) > 50:
    print(f'... and {len(missing) - 50} more')

# Also show a few that match (to verify the comparison works)
common = arabic_titles & cimafre_titles
print(f'\n== Common movies: {len(common)} ==')
for t in sorted(common)[:5]:
    print(t)
