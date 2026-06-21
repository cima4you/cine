import json, re

with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'r', encoding='utf-8') as f:
    sitemap = json.load(f)

# Search for specific remaining Asian items
search = ['kakegurui', 'kamen rider', 'dead talent', 'shin kamen']

print('Searching sitemap for remaining items:')
for term in search:
    found = False
    for m in sitemap:
        if term in m['name'].lower():
            print('  "{}" found: name="{}" year={}'.format(term, m['name'], m['year']))
            found = True
    if not found:
        # Check URL slugs too
        for m in sitemap:
            slug = m['url'].split('/')[-2] if m['url'].endswith('/') else m['url'].split('/')[-1]
            slug = slug.lower().replace('%d9%81%d9%8a%d9%84%d9%85-', '')
            if term in slug:
                print('  "{}" found in URL: slug="{}" name="{}" year={}'.format(term, slug[:50], m['name'], m['year']))
                found = True
                break
    
    if not found:
        print('  "{}" NOT found in sitemap'.format(term))

# Also check the Asian category listing for these
print('\nSearching Asian listings for remaining items...')
import requests
headers = {'User-Agent': 'Mozilla/5.0'}
CATEGORY = 'https://tuktukhd.com/category/movies-2/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d8%b3%d9%8a%d9%88%d9%8a'
FILM_PATTERN = r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+'

# Check first 5 pages
for page in range(1, 6):
    url = '{}page/{}/'.format(CATEGORY, page) if page > 1 else CATEGORY
    try:
        r = requests.get(url, timeout=15, headers=headers)
        alts = re.findall(r'alt="([^"]+)"', r.text)
        hrefs = re.findall(FILM_PATTERN, r.text, re.IGNORECASE)
        for alt, href in zip(alts, hrefs):
            alt = alt.strip()
            m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم', alt)
            if m:
                name = m.group(1).strip().lower()
                year = m.group(2)
                if 'kakegurui' in name or 'kamen' in name or 'dead talent' in name or 'shin' in name:
                    print('  FOUND ON ASIAN PAGE {}: "{}" ({})'.format(page, m.group(1).strip(), year))
    except:
        pass
