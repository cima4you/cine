import requests, re, json, concurrent.futures, base64, sys

headers = {'User-Agent': 'Mozilla/5.0'}

# Load data.js
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

# Load Asian index
with open('scripts/tuktukhd/data/tuktuk_asian_index.json', 'r', encoding='utf-8') as f:
    asian_index = json.load(f)

# Build existing lookup
def norm(t):
    t = t.lower().strip()
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t

existing = set()
for item in data_js:
    existing.add((norm(item.get('title', '')), str(item.get('year', ''))))

# Find new movies
new_movies = []
for m in asian_index:
    key = (norm(m['name']), m['year'])
    if key not in existing:
        # Also track by URL to avoid duplicates in index
        new_movies.append(m)
        existing.add(key)  # prevent duplicates within the new list

print('New Asian movies to add: {}'.format(len(new_movies)))

if not new_movies:
    sys.exit(0)

# How many to process
limit = 100
if len(sys.argv) > 1:
    limit = int(sys.argv[1])

new_movies = new_movies[:limit]
print('Processing first {}...'.format(len(new_movies)))

# Visit pages and extract data
def extract(m):
    try:
        r = requests.get(m['url'], timeout=20, headers=headers)
        text = r.text
        
        # Watch URL from data-crypt
        crypts = re.findall(r'data-crypt="([^"]+)"', text)
        watch_urls = []
        for c in crypts:
            try:
                watch_urls.append(base64.b64decode(c).decode('utf-8'))
            except:
                pass
        
        # Download URLs
        dl_links = re.findall(r'data-real-url="([^"]+)"', text)
        
        # Server name
        si = re.findall(r'<li[^>]*class="[^"]*server--item[^"]*"[^>]*>.*?<span>([^<]*)</span>', text, re.DOTALL)
        
        # Poster
        poster = ''
        pm = re.search(r'<img[^>]*src="([^"]+)"[^>]*alt="[^"]*{}'.format(re.escape(m['name'][:20])), text, re.IGNORECASE)
        if pm:
            poster = pm.group(1)
        if not poster:
            pm = re.search(r'class="[^"]*poster[^"]*"[^>]*src="([^"]+)"', text)
            if pm:
                poster = pm.group(1)
        
        # Description
        desc = ''
        dm = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', text)
        if dm:
            desc = dm.group(1)[:300]
        
        success = len(watch_urls) > 0 and len(dl_links) > 0
        sname = si[0].strip() if si else 'TukTuk Vip'
        
        return {
            'name': m['name'],
            'year': m['year'],
            'url': m['url'],
            'watch_urls': watch_urls,
            'server_name': sname,
            'download_urls': dl_links,
            'poster': poster,
            'description': desc,
            'success': success
        }
    except Exception as e:
        return {'name': m['name'], 'success': False, 'error': str(e)}

print('Visiting pages (10 parallel)...')
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    futures = [ex.submit(extract, m) for m in new_movies]
    for i, future in enumerate(concurrent.futures.as_completed(futures)):
        results.append(future.result())
        if (i + 1) % 20 == 0 or i + 1 == len(new_movies):
            print('  {}/{} done'.format(i + 1, len(new_movies)))

successful = [r for r in results if r.get('success')]
print('Success: {}, Failed: {}'.format(len(successful), len(results) - len(successful)))

# Add to data.js
added = 0
for r in successful:
    servers = [{'name': r['server_name'], 'url': r['watch_urls'][0], 'isDefault': True}]
    # Add alternate watch URLs as additional servers
    seen_names = {r['server_name']}
    for i, wu in enumerate(r['watch_urls'][1:], 2):
        sname = 'TukTuk {}'.format(i)
        if sname not in seen_names:
            servers.append({'name': sname, 'url': wu})
            seen_names.add(sname)
    
    download_servers = [{'name': 'TukTuk Download', 'url': dl} for dl in r['download_urls']]
    
    new_item = {
        'title': r['name'],
        'year': r['year'],
        'type': 'أسيوي',
        'servers': servers,
        'downloadServers': download_servers,
        'trial': '',
        'contentType': 'movie',
    }
    if r['poster']:
        new_item['poster'] = r['poster']
    if r['description']:
        new_item['description'] = r['description']
    
    data_js.append(new_item)
    added += 1

print('Added: {} items'.format(added))

if added > 0:
    prefix = content[:content.index('[')]
    suffix = content[content.rindex(']') + 1:]
    json_str = json.dumps(data_js, ensure_ascii=False)
    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(prefix + json_str + suffix)
    print('Saved data.js ({} items)'.format(len(data_js)))
