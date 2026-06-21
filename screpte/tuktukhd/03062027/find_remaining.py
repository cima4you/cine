import requests, re, json, base64, urllib.parse

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

target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']

# Find remaining items with multi-quality servers
remaining = []
for idx, item in enumerate(data_js):
    if any(s.get('name', '') in target_servers for s in item.get('servers', [])):
        remaining.append({
            'idx': idx,
            'title': item.get('title', '').strip(),
            'year': str(item.get('year', '')),
            'type': item.get('type', '')
        })

print('Remaining items to find: {}'.format(len(remaining)))

# Try aggressive search on tuktukhd
# For each remaining item, search the sitemap more aggressively
def super_slugify(title):
    t = title.lower().strip()
    t = re.sub(r'\s+\d{4}$', '', t)
    # Remove all special characters
    t = re.sub(r"[`'’‘:.,!?&/\-]", ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    # Return multiple variations
    result = [t]
    # Remove words like "the", "a", "an"
    for prefix in ['the ', 'a ', 'an ']:
        if t.startswith(prefix):
            result.append(t[len(prefix):])
            break
    # First word only (might work for some titles)
    first_word = t.split()[0] if t.split() else t
    result.append(first_word)
    return result

matched_remaining = []
still_unmatched = []

for r in remaining:
    found = False
    for tuktuk_item in sitemap_index:
        tuktuk_name = tuktuk_item['name'].lower().strip()
        tuktuk_year = tuktuk_item['year']
        
        if r['year'] != tuktuk_year:
            continue
        
        # Try various matching strategies
        r_norm = re.sub(r"[`'’‘:.,!?&/\-]", '', r['title'].lower().strip()).strip()
        r_norm = re.sub(r'\s+\d{4}$', '', r_norm)
        t_norm = re.sub(r"[`'’‘:.,!?&/\-]", '', tuktuk_name).strip()
        
        # Check if one is substring of the other
        if r_norm == t_norm:
            found = True
        elif r_norm in t_norm or t_norm in r_norm:
            # Check length ratio to avoid false matches
            longer = max(len(r_norm), len(t_norm))
            shorter = min(len(r_norm), len(t_norm))
            if shorter > 0 and shorter / longer > 0.5:
                found = True
        
        if found:
            matched_remaining.append({
                'data_title': r['title'],
                'data_year': r['year'],
                'data_type': r['type'],
                'tuktuk_name': tuktuk_item['name'],
                'tuktuk_url': tuktuk_item['url']
            })
            break
    
    if not found:
        still_unmatched.append(r)

print('Newly matched: {}'.format(len(matched_remaining)))
print('Still unmatched: {}'.format(len(still_unmatched)))

if matched_remaining:
    print('\nNew matches:')
    for m in matched_remaining:
        print('  "{}" ({}) [{}] <- "{}"'.format(
            m['data_title'], m['data_year'], m['data_type'], m['tuktuk_name']))

if still_unmatched:
    print('\nStill unmatched:')
    for m in still_unmatched:
        print('  "{}" ({}) [{}]'.format(m['title'], m['year'], m['type']))

# Try to visit newly matched pages and extract servers
if matched_remaining:
    print('\nVisiting {} newly matched pages...'.format(len(matched_remaining)))
    
    def extract(item):
        try:
            r = requests.get(item['tuktuk_url'], timeout=20, headers=headers)
            crypts = re.findall(r'data-crypt="([^"]+)"', r.text)
            watch_urls = []
            for c in crypts:
                try:
                    watch_urls.append(base64.b64decode(c).decode('utf-8'))
                except:
                    pass
            dl_links = re.findall(r'data-real-url="([^"]+)"', r.text)
            si = re.findall(r'<li[^>]*class="[^"]*server--item[^"]*"[^>]*>.*?<span>([^<]*)</span>', r.text, re.DOTALL)
            server_name = si[0].strip() if si else 'TukTuk Vip'
            return {
                'idx': item['data_title'],
                'data_title': item['data_title'],
                'data_year': item['data_year'],
                'data_type': item['data_type'],
                'tuktuk_url': item['tuktuk_url'],
                'watch_url': watch_urls[0] if watch_urls else None,
                'server_name': server_name,
                'download_urls': dl_links,
                'success': len(watch_urls) > 0
            }
        except Exception as e:
            return {'data_title': item['data_title'], 'success': False, 'error': str(e)}
    
    import concurrent.futures
    new_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(extract, m) for m in matched_remaining]
        for future in concurrent.futures.as_completed(futures):
            new_results.append(future.result())
    
    new_success = [r for r in new_results if r.get('success')]
    print('New success: {}, Failed: {}'.format(len(new_success), len(new_results) - len(new_success)))
    
    if new_success:
        # Update data_js
        updated = 0
        for r in new_success:
            # Find the matching item by title+year+type
            for item in data_js:
                if (item.get('title', '').strip() == r['data_title'] and 
                    str(item.get('year', '')) == r['data_year'] and
                    item.get('type', '') == r['data_type']):
                    
                    new_server = {
                        'name': r['server_name'],
                        'url': r['watch_url'],
                        'isDefault': True
                    }
                    new_downloads = [{'name': 'TukTuk Download', 'url': dl} for dl in r.get('download_urls', [])]
                    
                    old_servers = item.get('servers', [])
                    item['servers'] = [s for s in old_servers if s.get('name', '') not in target_servers]
                    item['servers'].insert(0, new_server)  # Add as first/default server
                    
                    if new_downloads:
                        item['downloadServers'] = new_downloads
                    
                    updated += 1
                    print('  Updated: "{}" ({})'.format(r['data_title'], r['data_year']))
                    break
        
        print('\nUpdated {} items'.format(updated))
        
        # Save updated data.js
        with open('data.js', 'r', encoding='utf-8') as f:
            full_content = f.read()
        prefix = full_content[:full_content.index('[')]
        suffix = full_content[full_content.rindex(']') + 1:]
        json_str = json.dumps(data_js, ensure_ascii=False)
        with open('data.js', 'w', encoding='utf-8') as f:
            f.write(prefix + json_str + suffix)
        print('Saved data.js')
