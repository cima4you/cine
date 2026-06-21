import json

# Load scraped index
with open('scripts/tuktukhd/data/tuktuk_index.json', 'r', encoding='utf-8') as f:
    index = json.load(f)

# Check for specific movies
needles = ['cuckoo', 'erupcja', 'josh johnson', 'snow white', 'minecraft', 'karate kid']
for item in index:
    title_lower = item['title'].lower()
    for n in needles:
        if n in title_lower:
            print('Found "{}": title="{}" year={} url={}'.format(n, item['title'], item['year'], item['url'][:60]))
            break

# Build lookup
lookup = {}
for item in index:
    t = item['title'].lower().strip()
    y = item['year']
    key = (t, y)
    if key not in lookup:
        lookup[key] = []
    lookup[key].append(item['url'])

# Check specific keys
search_keys = [('erupcja', '2026'), ('cuckoo', '2024'), ('josh johnson: symphony', '2026')]
for sk in search_keys:
    if sk in lookup:
        print('Key {} found! -> {}'.format(sk, lookup[sk]))
    else:
        print('Key {} NOT found'.format(sk))
        # Find similar keys
        for k in lookup:
            if k[0].startswith(sk[0][:3]):
                print('  Similar: {}'.format(k))

# Show all unique years and count
years = {}
for item in index:
    y = item['year']
    years[y] = years.get(y, 0) + 1
print('\nYears distribution:')
for y, c in sorted(years.items()):
    print('  {}: {}'.format(y, c))

# Show total unique keys
print('\nTotal unique (title, year) keys: {}'.format(len(lookup)))
