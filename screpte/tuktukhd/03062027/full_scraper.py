import requests, re, json, concurrent.futures, base64, sys, time

headers = {'User-Agent': 'Mozilla/5.0'}
BASE = 'https://tuktukhd.com/category/movies-2/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d8%ac%d9%86%d8%a8%d9%8a'
# URL-encoded "فيلم" = %D9%81%D9%8A%D9%84%D9%85
FILM_PATTERN = r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+'

def scrape_listing_page(page):
    url = '{}page/{}/'.format(BASE, page) if page > 1 else BASE
    try:
        r = requests.get(url, timeout=20, headers=headers, allow_redirects=True)
        if r.status_code != 200:
            return []
        alts = re.findall(r'alt="([^"]+)"', r.text)
        hrefs = re.findall(FILM_PATTERN, r.text, re.IGNORECASE)
        results = []
        for alt, href in zip(alts, hrefs):
            alt = alt.strip()
            m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم', alt)
            if m:
                eng_name = m.group(1).strip()
                year = m.group(2)
                results.append({
                    'title': eng_name,
                    'year': year,
                    'url': href
                })
        return results
    except Exception as e:
        return []

# Load data.js
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

# Extract items needing update (any type with multi-quality servers)
target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']

items_to_update = []
for item in data_js:
    servers = item.get('servers', [])
    has_multi = any(s.get('name', '') in target_servers for s in servers)
    if has_multi:
        title = item.get('title', '').strip()
        year = str(item.get('year', ''))
        items_to_update.append({
            'data_index': data_js.index(item),
            'title': title,
            'year': year,
            'item_type': item.get('type', ''),
            'old_servers': [s for s in servers if s.get('name', '') in target_servers],
            'other_servers': [s for s in servers if s.get('name', '') not in target_servers],
            'has_download': bool(item.get('downloadServers')),
            'old_downloads': item.get('downloadServers', [])
        })

print('Items needing update: {}'.format(len(items_to_update)))
print('Types:')
types_count = {}
for it in items_to_update:
    t = it['item_type']
    types_count[t] = types_count.get(t, 0) + 1
for t, c in sorted(types_count.items()):
    print('  {}: {}'.format(t, c))

# Normalize title for matching
def norm_title(title):
    title = title.strip()
    # Remove trailing year if present
    title = re.sub(r'\s+\d{4}$', '', title)
    return title.lower().strip()

# Build a lookup: (normalized_title, year) → items
update_lookup = {}
for it in items_to_update:
    t = norm_title(it['title'])
    y = it['year']
    key = (t, y)
    if key not in update_lookup:
        update_lookup[key] = []
    update_lookup[key].append(it)

print('\nUnique title+year keys: {}'.format(len(update_lookup)))

# Scrape listing pages to build tuktukhd index
print('Scraping tuktukhd listing pages...')
all_listed = []
page = 1
empty_pages = 0
while empty_pages < 3 and page <= 100:  # Max 100 pages
    page_movies = scrape_listing_page(page)
    if not page_movies:
        empty_pages += 1
    else:
        empty_pages = 0
        all_listed.extend(page_movies)
        if page % 20 == 0 or page == 1:
            print('  Page {}: {} listings (total: {})'.format(page, len(page_movies), len(all_listed)))
    page += 1

print('Total tuktukhd listings: {} (from {} pages)'.format(len(all_listed), page - 1))

# Build tuktukhd index: (normalized_title, year) → url
tuktuk_index = {}
for m in all_listed:
    t = m['title'].lower().strip()
    y = m['year']
    key = (t, y)
    if key not in tuktuk_index:
        tuktuk_index[key] = []
    tuktuk_index[key].append(m['url'])

# Match
matched = []
for key, items in update_lookup.items():
    norm_t, y = key
    tuktuk_urls = tuktuk_index.get(key, [])
    if tuktuk_urls:
        for it in items:
            matched.append({
                'data_item': it,
                'tuktuk_url': tuktuk_urls[0]
            })
    # Also try without year in title
    # If data.js title has year appended (e.g., "Movie Name 2024"), 
    # try matching without it
    alt_key = (norm_t, y)
    if alt_key not in tuktuk_index:
        # Try matching with just the title part (year might be embedded differently)
        for tk, tv in tuktuk_index.items():
            if tk[1] == y and tk[0].startswith(norm_t):
                for it in items:
                    matched.append({
                        'data_item': it,
                        'tuktuk_url': tv[0]
                    })
                break

print('\nMatched items: {}'.format(len(matched)))
print('Unmatched items: {}'.format(len(items_to_update) - len(matched)))

# Show unmatched items
matched_titles = set(m['data_item']['title'] for m in matched)
for it in items_to_update:
    if it['title'] not in matched_titles:
        print('  UNMATCHED: "{}" ({}) [{}]'.format(it['title'], it['year'], it['item_type']))

# Save match results
with open('scripts/tuktukhd/data/tuktuk_matched.json', 'w', encoding='utf-8') as f:
    json.dump(matched, f, ensure_ascii=False, indent=2)

# Now visit matched pages to extract servers
print('\nVisiting matched movie pages...')

def extract_servers(url):
    try:
        r = requests.get(url, timeout=20, headers=headers)
        # Extract watch server from data-crypt
        crypts = re.findall(r'data-crypt="([^"]+)"', r.text)
        watch_servers = []
        for c in crypts:
            try:
                decoded = base64.b64decode(c).decode('utf-8')
                watch_servers.append(decoded)
            except:
                pass
        
        # Extract download servers from data-real-url
        dl_links = re.findall(r'data-real-url="([^"]+)"', r.text)
        
        # Extract server name
        names = re.findall(r'<span>\s*([^<]+?)\s*</span>', r.text)
        server_name = ''
        for n in names:
            n = n.strip()
            if n and n != 'TukTuk' and n != 'جودة الفيلم :':
                server_name = n
        
        return {
            'watch_servers': watch_servers,
            'download_links': dl_links,
            'server_name': server_name or 'TukTuk Vip'
        }
    except Exception as e:
        return None

# Visit pages in parallel
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    futures = {ex.submit(extract_servers, m['tuktuk_url']): m for m in matched}
    for future in concurrent.futures.as_completed(futures):
        m = futures[future]
        try:
            result = future.result()
            m['server_data'] = result
        except Exception as e:
            m['server_data'] = None

# Build merge results
results = []
success = 0
fail = 0
for m in matched:
    sd = m.get('server_data')
    if sd and sd.get('watch_servers'):
        item = m['data_item']
        # Build new servers list: replace old multi-quality with new TukTuk
        new_server = {
            'name': sd['server_name'],
            'url': sd['watch_servers'][0],
            'isDefault': True
        }
        
        # Build new download servers
        new_downloads = []
        for dl_url in sd.get('download_links', []):
            new_downloads.append({
                'name': 'TukTuk Download',
                'url': dl_url
            })
        
        # New item data
        new_item = {
            'title': item['title'],
            'year': int(item['year']) if item['year'].isdigit() else item['year'],
            'type': item['item_type'],
            'servers': [new_server],
            'downloadServers': new_downloads if new_downloads else item.get('old_downloads', [])
        }
        
        # Add the item's other attributes that should be preserved
        results.append(new_item)
        success += 1
    else:
        fail += 1

print('\nResults: {} successful, {} failed'.format(success, fail))

if results:
    with open('scripts/tuktuk_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print('Saved to scripts/tuktuk_results.json')
    print('\nSample result:')
    print(json.dumps(results[0], ensure_ascii=False, indent=2))
