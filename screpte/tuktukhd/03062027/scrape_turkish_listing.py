import requests, re, json

CATEGORY = 'https://tuktukhd.com/category/%D8%AA%D8%B1%D9%83%D9%8A'
headers = {'User-Agent': 'Mozilla/5.0'}

# Scrape first 50 pages to see total
all_movies = []
for page in range(1, 51):
    url = '{}page/{}/'.format(CATEGORY, page) if page > 1 else CATEGORY
    r = requests.get(url, headers=headers, timeout=15)
    hrefs = re.findall(r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+', r.text)
    alts = re.findall(r'alt="([^"]+)"', r.text)
    if not hrefs:
        print('No more movies at page {}'.format(page))
        break
    # Pair alts with hrefs
    for alt, href in zip(alts[:len(hrefs)], hrefs):
        m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+(?:مترجم|مدبلج)', alt)
        if m:
            all_movies.append({'name': m.group(1).strip(), 'year': m.group(2), 'alt': alt[:60], 'url': href})
    print('Page {}: {} movies (total: {})'.format(page, len(hrefs), len(all_movies)))

print('\nTotal Turkish movies found: {}'.format(len(all_movies)))

# Count by year
years = {}
for m in all_movies:
    years[m['year']] = years.get(m['year'], 0) + 1
print('By year:')
for y in sorted(years.keys()):
    print(f'  {y}: {years[y]}')

# Save
with open('scripts/tuktukhd/data/turkish_listing.json', 'w', encoding='utf-8') as f:
    json.dump(all_movies, f, ensure_ascii=False, indent=2)
print('Saved to turkish_listing.json')
