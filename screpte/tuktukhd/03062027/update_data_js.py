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

# Build tuktuk lookup
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

# Find all items needing update
def slugify(title):
    t = title.lower().strip()
    t = re.sub(r'\s+\d{4}$', '', t)
    variations = [t]
    t_clean = re.sub(r"[`'’‘]", '', t)
    variations.append(t_clean)
    t_clean2 = re.sub(r"[`'’‘:.,!?]", '', t)
    variations.append(t_clean2)
    t_and = t.replace('&', 'and')
    variations.append(t_and)
    t_alnum = re.sub(r'[^a-zA-Z0-9\s]', '', t)
    variations.append(t_alnum)
    return variations

items_to_update = []
for idx, item in enumerate(data_js):
    servers = item.get('servers', [])
    if any(s.get('name', '') in target_servers for s in servers):
        title = item.get('title', '').strip()
        year = str(item.get('year', ''))
        nt = norm_title(title)
        key = (nt, year)
        
        url = None
        if key in tuktuk_lookup:
            url = tuktuk_lookup[key][0]
        else:
            for variation in slugify(title):
                fkey = (variation, year)
                if fkey in tuktuk_lookup:
                    url = tuktuk_lookup[fkey][0]
                    break
        
        items_to_update.append({
            'idx': idx,
            'title': title,
            'year': year,
            'type': item.get('type', ''),
            'url': url
        })

print('Items needing update: {}'.format(len(items_to_update)))
has_url = [i for i in items_to_update if i['url']]
no_url = [i for i in items_to_update if not i['url']]
print('With URL: {}, Without URL: {}'.format(len(has_url), len(no_url)))

if no_url:
    print('\nNo URL found for:')
    for i in no_url:
        print('  "{}" ({}) [{}]'.format(i['title'], i['year'], i['type']))

if not has_url:
    print('No items with URLs to scrape. Exiting.')
    sys.exit(0)

# Visit pages to extract servers
print('\nVisiting {} pages...'.format(len(has_url)))

def extract_servers(item):
    try:
        r = requests.get(item['url'], timeout=20, headers=headers)
        crypts = re.findall(r'data-crypt="([^"]+)"', r.text)
        watch_urls = []
        for c in crypts:
            try:
                watch_urls.append(base64.b64decode(c).decode('utf-8'))
            except:
                pass
        
        dl_links = re.findall(r'data-real-url="([^"]+)"', r.text)
        
        server_name = 'TukTuk Vip'
        si = re.findall(r'<li[^>]*class="[^"]*server--item[^"]*"[^>]*>.*?<span>([^<]*)</span>', r.text, re.DOTALL)
        if si:
            server_name = si[0].strip()
        
        return {
            'idx': item['idx'],
            'title': item['title'],
            'year': item['year'],
            'type': item['type'],
            'watch_url': watch_urls[0] if watch_urls else None,
            'server_name': server_name or 'TukTuk Vip',
            'download_urls': dl_links,
            'success': len(watch_urls) > 0
        }
    except Exception as e:
        return {'idx': item['idx'], 'success': False, 'error': str(e)}

results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    futures = [ex.submit(extract_servers, item) for item in has_url]
    done = 0
    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        results.append(result)
        done += 1

successful = [r for r in results if r.get('success')]
print('Success: {}, Failed: {}'.format(len(successful), len(results) - len(successful)))

# Apply updates to data_js
updated_count = 0
for r in successful:
    idx = r['idx']
    item = data_js[idx]
    
    new_server = {
        'name': r['server_name'],
        'url': r['watch_url'],
        'isDefault': True
    }
    
    new_downloads = [{'name': 'TukTuk Download', 'url': dl} for dl in r.get('download_urls', [])]
    
    # Replace multi-quality servers with new TukTuk server
    old_servers = item.get('servers', [])
    filtered_servers = [s for s in old_servers if s.get('name', '') not in target_servers]
    
    # If all servers were multi-quality, just use the new one
    # If there were other servers, add the new one alongside them
    if not filtered_servers:
        # All servers were multi-quality, replace entirely
        item['servers'] = [new_server]
    else:
        # Replace first multi-quality with new server, keep others
        replaced = False
        new_list = []
        for s in old_servers:
            if s.get('name', '') in target_servers and not replaced:
                new_list.append(new_server)
                replaced = True
            elif s.get('name', '') not in target_servers:
                new_list.append(s)
        # If there are remaining multi-quality servers beyond the first, drop them
        item['servers'] = new_list
    
    # Update download servers if we got any
    if new_downloads:
        item['downloadServers'] = new_downloads
    
    updated_count += 1

print('\nUpdated {} items in data.js'.format(updated_count))

# Save updated data.js
prefix = content[:start]
suffix = content[end:]
json_str = json.dumps(data_js, ensure_ascii=False)
with open('data.js', 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)

import os
print('File size: {} KB'.format(os.path.getsize('data.js') / 1024))
print('Total items: {}'.format(len(data_js)))
