import json

with open('scripts/tuktukhd/data/tuktuk_index.json', 'r', encoding='utf-8') as f:
    index = json.load(f)

# Year distribution
years = {}
for item in index:
    y = item['year']
    years[y] = years.get(y, 0) + 1
print('Year distribution in tuktuk index (100 pages):')
for y, c in sorted(years.items()):
    print('  {}: {}'.format(y, c))

# Check for specific movies
check_titles = ['snow white', 'minecraft', 'karate kid', 'cuckoo', 'queen of the ring',
                'first omen', 'final destination', 'lilo', 'road trip 2000',
                'william tell', 'the amateur', 'mickey 17', 'wolf man']
print('\nLooking for specific movies:')
for item in index:
    t = item['title'].lower()
    for ct in check_titles:
        if ct in t:
            print('  "{}" ({}) - {}'.format(item['title'], item['year'], item['url'][:50]))
            break

# Also check the items_to_update for titles that should exist
# Load data.js
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']

multi_items = []
for item in data_js:
    servers = item.get('servers', [])
    if any(s.get('name', '') in target_servers for s in servers):
        title = item.get('title', '').strip()
        year = str(item.get('year', ''))
        multi_items.append((title, year, item.get('type', '')))

# Check what years these span
multi_years = {}
for t, y, tp in multi_items:
    multi_years[y] = multi_years.get(y, 0) + 1
print('\nMulti-quality items by year:')
for y, c in sorted(multi_years.items()):
    print('  {}: {}'.format(y, c))

# Check if any of them are in the index
import re
def norm_title(title):
    title = re.sub(r'\s+\d{4}$', '', title.strip())
    return title.lower().strip()

matched_count = 0
for t, y, tp in multi_items:
    nt = norm_title(t)
    for item in index:
        if item['title'].lower() == nt and item['year'] == y:
            matched_count += 1
            break

print('\nOf {} multi-quality items, {} found in first 100 pages'.format(len(multi_items), matched_count))
