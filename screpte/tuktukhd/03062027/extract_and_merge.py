import requests, re, json, concurrent.futures, base64, urllib.parse, sys

headers = {'User-Agent': 'Mozilla/5.0'}

# Load data.js
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

# Load sitemap index
with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'r', encoding='utf-8') as f:
    sitemap_index = json.load(f)

# Build comprehensive lookup
target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']

def norm_title(t):
    return re.sub(r'\s+\d{4}$', '', t.lower().strip())

def norm_tuktuk_name(n):
    return n.lower().strip()

tuktuk_lookup = {}
for f in sitemap_index:
    key = (norm_tuktuk_name(f['name']), f['year'])
    if key not in tuktuk_lookup:
        tuktuk_lookup[key] = []
    tuktuk_lookup[key].append(f['url'])

print('Tuktuk lookup keys: {}'.format(len(tuktuk_lookup)))

# Collect all multi-quality items with their indices
multi_items = []
for idx, item in enumerate(data_js):
    servers = item.get('servers', [])
    if any(s.get('name', '') in target_servers for s in servers):
        title = item.get('title', '').strip()
        year = str(item.get('year', ''))
        multi_items.append({
            'idx': idx,
            'title': title,
            'year': year,
            'type': item.get('type', '')
        })

print('Multi-quality items: {}'.format(len(multi_items)))

# Try to find URL for each (exact + fuzzy)
def slugify(title):
    """Convert title to possible URL slug variations"""
    t = title.lower().strip()
    # Remove trailing year
    t = re.sub(r'\s+\d{4}$', '', t)
    # Different slug variations
    variations = []
    # Direct match
    variations.append(t)
    # Remove special characters
    t_clean = re.sub(r"[`'’‘]", '', t)  # Remove apostrophes
    variations.append(t_clean)
    t_clean2 = re.sub(r"[`'’‘:.,!?]", '', t)
    variations.append(t_clean2)
    # Replace & with and
    t_and = t.replace('&', 'and')
    variations.append(t_and)
    # Remove all non-alphanumeric except spaces
    t_alnum = re.sub(r'[^a-zA-Z0-9\s]', '', t)
    variations.append(t_alnum)
    return variations

matched_pages = []
unmatched = []
fuzzy_matched = 0

for m in multi_items:
    nt = norm_title(m['title'])
    y = m['year']
    key = (nt, y)
    
    if key in tuktuk_lookup:
        matched_pages.append({
            'idx': m['idx'],
            'title': m['title'],
            'year': y,
            'type': m['type'],
            'url': tuktuk_lookup[key][0],
            'match_type': 'exact'
        })
    else:
        # Try fuzzy matching
        found = False
        for variation in slugify(m['title']):
            fkey = (variation, y)
            if fkey in tuktuk_lookup:
                matched_pages.append({
                    'idx': m['idx'],
                    'title': m['title'],
                    'year': y,
                    'type': m['type'],
                    'url': tuktuk_lookup[fkey][0],
                    'match_type': 'fuzzy'
                })
                fuzzy_matched += 1
                found = True
                break
        if not found:
            unmatched.append(m)

print('Exact matched: {}'.format(len(matched_pages) - fuzzy_matched))
print('Fuzzy matched: {}'.format(fuzzy_matched))
print('Total matched: {}'.format(len(matched_pages)))
print('Unmatched: {}'.format(len(unmatched)))

# Show unmatched
if unmatched:
    print('\nUnmatched items:')
    for m in unmatched:
        print('  "{}" ({}) [{}]'.format(m['title'], m['year'], m['type']))

if len(matched_pages) == 0:
    print('No pages to visit. Exiting.')
    sys.exit(0)

# Visit pages in parallel to extract servers
print('\nVisiting {} pages to extract servers...'.format(len(matched_pages)))

def extract_servers(mp):
    try:
        r = requests.get(mp['url'], timeout=20, headers=headers)
        # Watch server from data-crypt
        crypts = re.findall(r'data-crypt="([^"]+)"', r.text)
        watch_urls = []
        for c in crypts:
            try:
                decoded = base64.b64decode(c).decode('utf-8')
                watch_urls.append(decoded)
            except:
                pass
        
        # Download servers
        dl_links = re.findall(r'data-real-url="([^"]+)"', r.text)
        
        # Server name from the active server item (li.server--item > span)
        server_name = 'TukTuk Vip'
        server_items = re.findall(r'<li[^>]*class="[^"]*server--item[^"]*"[^>]*>.*?<span>([^<]*)</span>', r.text, re.DOTALL)
        if server_items:
            server_name = server_items[0].strip()
        
        return {
            'idx': mp['idx'],
            'title': mp['title'],
            'year': mp['year'],
            'type': mp['type'],
            'watch_url': watch_urls[0] if watch_urls else '',
            'server_name': server_name or 'TukTuk Vip',
            'download_urls': dl_links,
            'success': len(watch_urls) > 0
        }
    except Exception as e:
        return {
            'idx': mp['idx'],
            'title': mp['title'],
            'year': mp['year'],
            'type': mp['type'],
            'success': False,
            'error': str(e)
        }

results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    futures = [ex.submit(extract_servers, mp) for mp in matched_pages]
    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        results.append(result)

results.sort(key=lambda r: r['idx'])

success = sum(1 for r in results if r.get('success'))
print('Visited: {}, Success: {}, Failed: {}'.format(len(results), success, len(results) - success))

# Generate merge results JSON
merge_results = []
for r in results:
    if r.get('success'):
        # Build server entry
        new_item = {
            'title': r['title'],
            'year': int(r['year']) if r['year'].isdigit() else r['year'],
            'type': r['type'],
            'servers': [{
                'name': r['server_name'],
                'url': r['watch_url'],
                'isDefault': True
            }],
            'downloadServers': [{
                'name': 'TukTuk Download',
                'url': dl
            } for dl in r.get('download_urls', [])]
        }
        merge_results.append(new_item)

print('Merge results: {} items'.format(len(merge_results)))

if merge_results:
    with open('scripts/tuktukhd/data/tuktuk_merge_results.json', 'w', encoding='utf-8') as f:
        json.dump(merge_results, f, ensure_ascii=False, indent=2)
    print('Saved to scripts/tuktuk_merge_results.json')
    
    print('\nSample result:')
    print(json.dumps(merge_results[0], ensure_ascii=False, indent=2))
    
    # Also count by type
    by_type = {}
    for r in merge_results:
        t = r['type']
        by_type[t] = by_type.get(t, 0) + 1
    print('\nBy type:')
    for t, c in sorted(by_type.items()):
        print('  {}: {}'.format(t, c))
