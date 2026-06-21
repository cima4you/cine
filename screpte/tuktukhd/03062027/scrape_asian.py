import requests, re, json, concurrent.futures, base64, urllib.parse, sys, time

headers = {'User-Agent': 'Mozilla/5.0'}
CATEGORY = 'https://tuktukhd.com/category/movies-2/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d8%b3%d9%8a%d9%88%d9%8a'
FILM_PATTERN = r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+'

print('Scraping Asian movies from tuktukhd...')

# Load existing sitemap index for ALL movies
with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'r', encoding='utf-8') as f:
    all_movies = json.load(f)
print('Existing sitemap index: {} movies'.format(len(all_movies)))

# First check if Asian category has different movies than sitemap
def scrape_category_page(url):
    try:
        r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        if r.status_code != 200:
            return []
        alts = re.findall(r'alt="([^"]+)"', r.text)
        hrefs = re.findall(FILM_PATTERN, r.text, re.IGNORECASE)
        results = []
        for alt, href in zip(alts, hrefs):
            alt = alt.strip()
            m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم', alt)
            if m:
                results.append({
                    'name': m.group(1).strip(),
                    'year': m.group(2),
                    'url': href
                })
        return results
    except:
        return []

# Scrape first 50 pages of Asian category
all_asian = []
for page in range(1, 51):
    url = '{}page/{}/'.format(CATEGORY, page) if page > 1 else CATEGORY
    entries = scrape_category_page(url)
    if not entries and page > 1:
        break
    all_asian.extend(entries)
    if page % 10 == 0 or page == 1:
        print('  Page {}: {} (total: {})'.format(page, len(entries), len(all_asian)))
    time.sleep(0.2)

print('\nAsian category movies: {} from {} pages'.format(len(all_asian), page))

# Check which ones are NOT in sitemap index
sitemap_urls = set(m['url'] for m in all_movies)
not_in_sitemap = [m for m in all_asian if m['url'] not in sitemap_urls]
print('Asian movies NOT in sitemap: {}'.format(len(not_in_sitemap)))

# Check remaining unmatched items
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']

# Find remaining multi-quality items by type
remaining_by_type = {}
for item in data_js:
    if any(s.get('name', '') in target_servers for s in item.get('servers', [])):
        t = item.get('type', '')
        if t not in remaining_by_type:
            remaining_by_type[t] = []
        remaining_by_type[t].append({
            'title': item.get('title', '').strip(),
            'year': str(item.get('year', ''))
        })

print('\nRemaining multi-quality items by type:')
for t, items in sorted(remaining_by_type.items()):
    print('  {}: {} items'.format(t, len(items)))
    for i in items:
        print('    "{}" ({})'.format(i['title'], i['year']))

# Aggressive search in Asian category for remaining Asian items
asian_remaining = remaining_by_type.get('أسيوي', [])
print('\nSearching Asian category for remaining Asian items...')

def super_norm(t):
    t = t.lower().strip()
    t = re.sub(r'\s+\d{4}$', '', t)
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t

for r_item in asian_remaining:
    r_norm = super_norm(r_item['title'])
    found = False
    for asian in all_asian:
        a_norm = super_norm(asian['name'])
        if r_item['year'] == asian['year']:
            if r_norm == a_norm or r_norm in a_norm or a_norm in r_norm:
                print('  MATCH: "{}" ({}) <=> "{}" ({})'.format(
                    r_item['title'], r_item['year'], asian['name'], asian['year']))
                found = True
                break
    if not found:
        print('  NOT FOUND: "{}" ({})'.format(r_item['title'], r_item['year']))

# Also create Asian-specific sitemap index for this category
build_index = {}
for m in all_asian:
    key = (m['name'].lower().strip(), m['year'])
    if key not in build_index:
        build_index[key] = []
    build_index[key].append(m['url'])

print('\nAsian category unique keys: {}'.format(len(build_index)))

# Save Asian category index
with open('scripts/tuktukhd/data/tuktuk_asian_index.json', 'w', encoding='utf-8') as f:
    json.dump(all_asian, f, ensure_ascii=False, indent=2)
print('Saved to scripts/tuktuk_asian_index.json')
