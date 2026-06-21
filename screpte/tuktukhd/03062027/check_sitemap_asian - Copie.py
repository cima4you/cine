import requests, re, json, urllib.parse

# Check if the Asian movie URLs are in the sitemap
with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'r', encoding='utf-8') as f:
    sitemap = json.load(f)

# Check some Asian movie slugs against sitemap
asian_slugs = [
    'per-aspera-ad-astra',
    'a-foggy-tale',
    'omukade',
    'monay',
    'colony',
    'tunnels-sun-in-the-dark',
    'hayok',
    'panda-plan-the-magical-tribe',
    'janur-ireng',
    'human-resource',
]

print('Checking Asian slugs in sitemap:')
for slug in asian_slugs:
    found = False
    for m in sitemap:
        if slug in m['url'].lower():
            found = True
            break
    print('  {}: {}'.format(slug, 'FOUND' if found else 'NOT FOUND'))

# Also check by name
asian_names = ['Per Aspera Ad Astra', 'A Foggy Tale', 'Omukade', 'Monay', 'Colony', 'Hayok', 'Janur Ireng']
print('\nChecking Asian names in sitemap:')
for name in asian_names:
    norm_name = name.lower().strip()
    found = False
    for m in sitemap:
        if m['name'].lower().strip() == norm_name:
            found = True
            break
    print('  {}: {}'.format(name, 'FOUND' if found else 'NOT FOUND'))

# Total count
print('\nTotal sitemap entries: {}'.format(len(sitemap)))

# Check if maybe the sitemap uses a different URL encoding for Asian movies
# e.g., some might use Unicode directly instead of percent-encoding
# Also check total unique URLs
urls = set(m['url'] for m in sitemap)
print('Unique URLs in sitemap: {}'.format(len(urls)))
