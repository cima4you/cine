import requests, re, json, concurrent.futures, urllib.parse

headers = {'User-Agent': 'Mozilla/5.0'}

# Get all sitemap URLs from index
r = requests.get('https://tuktukhd.com/sitemap.xml', timeout=15, headers=headers)
sitemap_urls = re.findall(r'<loc>([^<]+)</loc>', r.text)
post_sitemaps = sorted([s for s in sitemap_urls if 'post-sitemap' in s])
print('Total post sitemaps: {}'.format(len(post_sitemaps)))

# Parse a sitemap and extract film URLs with English name and year
def parse_sitemap(url):
    try:
        r = requests.get(url, timeout=15, headers=headers)
        urls = re.findall(r'<loc>([^<]+)</loc>', r.text)
        films = []
        for u in urls:
            # Match film URLs: https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-{name}-{year}-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/
            m = re.search(r'/%D9%81%D9%8A%D9%84%D9%85-(.+?)-(\d{4})-%D9%85%D8%AA%D8%B1%D8%AC%D9%85', u, re.IGNORECASE)
            if m:
                eng_name_slug = m.group(1)
                year = m.group(2)
                # Decode URL-encoded name
                eng_name = urllib.parse.unquote(eng_name_slug)
                eng_name = eng_name.replace('-', ' ')
                films.append({
                    'name': eng_name,
                    'year': year,
                    'url': u
                })
        return films
    except Exception as e:
        return []

# Parse all sitemaps in parallel
all_films = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    futures = {ex.submit(parse_sitemap, url): url for url in post_sitemaps}
    done = 0
    for future in concurrent.futures.as_completed(futures):
        films = future.result()
        all_films.extend(films)
        done += 1
        if done % 20 == 0:
            print('  Processed {} / {} sitemaps ({} films so far)'.format(done, len(post_sitemaps), len(all_films)))

print('\nTotal films from sitemaps: {}'.format(len(all_films)))

# Save
with open('scripts/tuktukhd/data/tuktuk_sitemap_index.json', 'w', encoding='utf-8') as f:
    json.dump(all_films, f, ensure_ascii=False, indent=2)
print('Saved to scripts/tuktuk_sitemap_index.json')

# Load data.js and check matching
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']

multi_items = []
for item in data_js:
    servers = item.get('servers', [])
    if any(s.get('name', '') in target_servers for s in servers):
        title = item.get('title', '').strip()
        year = str(item.get('year', ''))
        multi_items.append({
            'title': title,
            'year': year,
            'type': item.get('type', '')
        })

def norm_title(t):
    return re.sub(r'\s+\d{4}$', '', t.lower().strip())

def norm_tuktuk_name(n):
    # Normalize tuktuk name: lowercase, strip special chars
    return n.lower().strip()

# Build tuktuk lookup: (norm_name, year) -> url
tuktuk_lookup = {}
for f in all_films:
    key = (norm_tuktuk_name(f['name']), f['year'])
    if key not in tuktuk_lookup:
        tuktuk_lookup[key] = []
    tuktuk_lookup[key].append(f['url'])

print('Tuktuk lookup keys: {}'.format(len(tuktuk_lookup)))

# Try matching
matched = []
unmatched = []
for m in multi_items:
    nt = norm_title(m['title'])
    y = m['year']
    key = (nt, y)
    if key in tuktuk_lookup:
        matched.append({
            'data_title': m['title'],
            'data_year': y,
            'data_type': m['type'],
            'tuktuk_url': tuktuk_lookup[key][0]
        })
    else:
        unmatched.append(m)

print('\nMatched: {} / {}'.format(len(matched), len(multi_items)))
print('Unmatched: {}'.format(len(unmatched)))

# Show some matches
if matched:
    print('\nSample matches:')
    for m in matched[:10]:
        print('  "{}" ({}) [{}] -> {}'.format(m['data_title'], m['data_year'], m['data_type'], m['tuktuk_url'][:60]))

# Show unmatched years
if unmatched:
    years = {}
    for m in unmatched:
        years[m['year']] = years.get(m['year'], 0) + 1
    print('\nUnmatched by year:')
    for y, c in sorted(years.items()):
        print('  {}: {}'.format(y, c))
    # Show first 10 unmatched
    print('\nFirst 10 unmatched:')
    for m in unmatched[:10]:
        print('  "{}" ({}) [{}]'.format(m['title'], m['year'], m['type']))
