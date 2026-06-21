import json

with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'r', encoding='utf-8') as f:
    sitemap = json.load(f)

# Show entries containing 'colony' or 'human'
print('Sitemap entries with "colony" or "human":')
for m in sitemap:
    if 'colony' in m['url'].lower() or 'human' in m['url'].lower():
        print('  name="{}" url={}'.format(m['name'], m['url'][:100]))

# Check first 10 entries to see what the name field looks like
print('\nFirst 10 sitemap entries:')
for m in sitemap[:10]:
    print('  name="{}" year={} url={}'.format(m['name'], m['year'], m['url'][:80]))

# Check what URL pattern is used for Asian movies specifically
# by looking at the Asian listing URLs from page 1
asian_urls = [
    'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-per-aspera-ad-astra-2026-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/',
    'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-a-foggy-tale-2025-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/'
]

print('\nChecking if Asian URLs match sitemap URL pattern:')
import re
for au in asian_urls:
    m = re.search(r'/%D9%81%D9%8A%D9%84%D9%85-(.+?)-(\d{4})-%D9%85%D8%AA%D8%B1%D8%AC%D9%85', au, re.IGNORECASE)
    if m:
        name_slug = m.group(1)
        year = m.group(2)
        print('  slug="{}" year={} -> checked in sitemap...'.format(name_slug, year))
        found = any(name_slug in s['url'] for s in sitemap)
        print('  Found: {}'.format(found))

# Maybe there are Asian movies from BEFORE the sitemap was generated
# and newer movies not yet indexed. The sitemap generation might be periodic.
# Let me check what year range the sitemap covers
years = {}
for m in sitemap:
    y = m['year']
    years[y] = years.get(y, 0) + 1
print('\nSitemap year distribution:')
for y, c in sorted(years.items()):
    print('  {}: {}'.format(y, c))
