import re, json

# Read cimafre movies
cimafre = json.load(open('data/data-cimafre.json', 'r', encoding='utf-8'))
cimafre_titles = set()
for m in cimafre:
    t = m.get('title_clean', '') or m.get('title', '')
    t = re.sub(r'^مشاهدة (فيلم|مسلسل|انمي)\s+', '', t)
    t = re.sub(r'\s+كامل اون لاين.*', '', t)
    cimafre_titles.add(t.strip().lower())

print(f'Cimafre movies: {len(cimafre_titles)}')

# Read data-arabic.js
with open('data/data-arabic.js', 'r', encoding='utf-8') as f:
    content = f.read()

# The data is: const cd_arabic = [...];
# Extract the array part
match = re.search(r'const cd_arabic = \[(.*)\];', content, re.DOTALL)
if not match:
    print("Could not find array!")
    exit()

array_text = '[' + match.group(1) + ']'
arabic_data = json.loads(array_text)

arabic_titles = set()
for m in arabic_data:
    t = m.get('title', '').strip()
    arabic_titles.add(t.strip().lower())

print(f'Arabic.js movies: {len(arabic_titles)}')

# Find movies in arabic.js but not in cimafre
missing = arabic_titles - cimafre_titles
print(f'\n== Arabic movies NOT in cimafre: {len(missing)} ==')
for t in sorted(missing):
    print(t)

# Common
common = arabic_titles & cimafre_titles
print(f'\n== Common movies: {len(common)} ==')
for t in sorted(common)[:10]:
    print(t)
