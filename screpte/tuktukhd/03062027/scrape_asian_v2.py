import requests, re, json, concurrent.futures, base64, time, sys

headers = {'User-Agent': 'Mozilla/5.0'}
CATEGORY = 'https://tuktukhd.com/category/movies-2/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d8%b3%d9%8a%d9%88%d9%8a'
FILM_PATTERN = r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+'

def scrape_listing(url):
    try:
        r = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'}, allow_redirects=True)
        if r.status_code != 200: return []
        alts = re.findall(r'alt="([^"]+)"', r.text)
        hrefs = re.findall(FILM_PATTERN, r.text, re.IGNORECASE)
        results = []
        for alt, href in zip(alts, hrefs):
            alt = alt.strip()
            m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم', alt)
            if m:
                results.append({'name': m.group(1).strip(), 'year': m.group(2), 'url': href})
        return results
    except:
        return []

print('Scraping all Asian category pages...')
all_listed = []
for page in range(1, 51):
    url = '{}page/{}/'.format(CATEGORY, page) if page > 1 else CATEGORY
    entries = scrape_listing(url)
    if not entries and page > 1: break
    all_listed.extend(entries)
    if page % 10 == 0 or page == 1:
        print('  Page {}: {} (total: {})'.format(page, len(entries), len(all_listed)))

print('Total Asian movies: {}'.format(len(all_listed)))

# Load data.js
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']

def norm(t):
    t = re.sub(r'\s+\d{4}$', '', t.lower().strip())
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t

# Find all items with multi-quality servers (all types, not just Asian)
items_to_update = []
for idx, item in enumerate(data_js):
    if any(s.get('name', '') in target_servers for s in item.get('servers', [])):
        title = item.get('title', '').strip()
        year = str(item.get('year', ''))
        items_to_update.append({
            'idx': idx, 'title': title, 'year': year, 'type': item.get('type', '')
        })

print('Items needing update (all types): {}'.format(len(items_to_update)))

# Build Asian lookup
asian_lookup = {}
for m in all_listed:
    key = (m['name'].lower().strip(), m['year'])
    if key not in asian_lookup:
        asian_lookup[key] = []
    asian_lookup[key].append(m['url'])

# Match all items against Asian category
matched = []
unmatched = []

for item in items_to_update:
    nt = norm(item['title'])
    y = item['year']
    key = (nt, y)
    
    found_url = None
    
    # Try exact match
    for ak, urls in asian_lookup.items():
        if ak[1] == y and (norm(ak[0]) == nt or norm(ak[0]) in nt or nt in norm(ak[0])):
            found_url = urls[0]
            break
    
    # Try URL-encoded variations
    if not found_url:
        for ak, urls in asian_lookup.items():
            if ak[1] == y:
                a_norm = norm(ak[0])
                if len(nt) > 3 and len(a_norm) > 3 and (nt[:5] in a_norm or a_norm[:5] in nt):
                    found_url = urls[0]
                    break
    
    if found_url:
        matched.append({**item, 'url': found_url})
    else:
        unmatched.append(item)

print('Matched in Asian category: {}'.format(len(matched)))
print('Unmatched: {}'.format(len(unmatched)))

# Show what types matched
from collections import Counter
matched_types = Counter(m['type'] for m in matched)
print('Matched by type:', dict(matched_types))

# If nothing matched, check what Asian movies we actually have
if len(matched) == 0:
    print('\nAsian category sample movies:')
    for m in all_listed[:5]:
        print('  "{}" ({})'.format(m['name'], m['year']))
    print('\nLooking for specific remaining items...')
    for item in unmatched:
        print('  Searching for: "{}" ({}) [{}]'.format(item['title'], item['year'], item['type']))
        # Check all Asian titles
        for am in all_listed:
            if item['year'] == am['year']:
                rn = norm(item['title'])
                an = norm(am['name'])
                if rn in an or an in rn:
                    print('    CLOSE: "{}"'.format(am['name']))
                    break
else:
    # Visit matched pages for servers
    print('\nVisiting {} pages...'.format(len(matched)))
    
    def extract(item):
        try:
            r = requests.get(item['url'], timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
            crypts = re.findall(r'data-crypt="([^"]+)"', r.text)
            watch_urls = [base64.b64decode(c).decode('utf-8') for c in crypts]
            dl_links = re.findall(r'data-real-url="([^"]+)"', r.text)
            si = re.findall(r'<li[^>]*class="[^"]*server--item[^"]*"[^>]*>.*?<span>([^<]*)</span>', r.text, re.DOTALL)
            sname = si[0].strip() if si else 'TukTuk Vip'
            return {
                'idx': item['idx'], 'title': item['title'], 'year': item['year'],
                'type': item['type'],
                'watch_url': watch_urls[0] if watch_urls else None,
                'server_name': sname,
                'download_urls': dl_links,
                'success': len(watch_urls) > 0
            }
        except Exception as e:
            return {'idx': item['idx'], 'success': False, 'error': str(e)}
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(extract, m) for m in matched]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    successful = [r for r in results if r.get('success')]
    print('Success: {}, Failed: {}'.format(len(successful), len(results) - len(successful)))
    
    # Update data_js
    updated = 0
    for r in successful:
        idx = r['idx']
        item = data_js[idx]
        new_server = {'name': r['server_name'], 'url': r['watch_url'], 'isDefault': True}
        new_downloads = [{'name': 'TukTuk Download', 'url': dl} for dl in r.get('download_urls', [])]
        
        old_servers = item.get('servers', [])
        item['servers'] = [s for s in old_servers if s.get('name', '') not in target_servers]
        item['servers'].insert(0, new_server)
        
        if new_downloads:
            item['downloadServers'] = new_downloads
        updated += 1
    
    print('Updated: {} items'.format(updated))
    
    if updated > 0:
        prefix = content[:content.index('[')]
        suffix = content[content.rindex(']') + 1:]
        json_str = json.dumps(data_js, ensure_ascii=False)
        with open('data.js', 'w', encoding='utf-8') as f:
            f.write(prefix + json_str + suffix)
        print('Saved data.js')
    
    # Final check
    remaining = sum(1 for item in data_js if any(s.get('name', '') in target_servers for s in item.get('servers', [])))
    print('Remaining multi-quality servers: {}'.format(remaining))
