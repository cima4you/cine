import requests, re, json, concurrent.futures, base64, sys

headers = {'User-Agent': 'Mozilla/5.0'}
CATEGORY = 'https://tuktukhd.com/category/movies-2/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d8%b3%d9%8a%d9%88%d9%8a'
FILM_PATTERN = r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+'

start_page = int(sys.argv[1]) if len(sys.argv) > 1 else 1
end_page = int(sys.argv[2]) if len(sys.argv) > 2 else start_page
per_page = int(sys.argv[3]) if len(sys.argv) > 3 else 999

print('Scraping Asian pages {} to {} ({} per page)...'.format(start_page, end_page, per_page))

def scrape_listing(url):
    try:
        r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        if r.status_code != 200: return []
        alts = re.findall(r'alt="([^"]+)"', r.text)
        hrefs = re.findall(FILM_PATTERN, r.text, re.IGNORECASE)
        results = []
        for alt, href in zip(alts, hrefs):
            alt = alt.strip()
            m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم', alt)
            if m:
                results.append({'name': m.group(1).strip(), 'year': m.group(2), 'url': href})
        return results[:per_page]
    except:
        return []

all_listed = []
for page in range(start_page, end_page + 1):
    url = '{}page/{}/'.format(CATEGORY, page) if page > 1 else CATEGORY
    entries = scrape_listing(url)
    if not entries and page > 1:
        break
    all_listed.extend(entries)
    print('  Page {}: {} (total: {})'.format(page, len(entries), len(all_listed)))

print('Total scraped: {}'.format(len(all_listed)))
if not all_listed:
    sys.exit(0)

# Load data.js for duplicate check
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

def norm(t):
    t = t.lower().strip()
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t

existing = set()
for item in data_js:
    existing.add((norm(item.get('title', '')), str(item.get('year', ''))))

new_movies = []
for m in all_listed:
    key = (norm(m['name']), m['year'])
    if key not in existing:
        new_movies.append(m)
        existing.add(key)

print('New (not in data.js): {}'.format(len(new_movies)))
if not new_movies:
    sys.exit(0)

def extract_details(text):
    """Extract movie details from tuktukhd page HTML"""
    details = {}
    
    # Watch URL
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
    
    # Poster from og:image
    poster = ''
    pm = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', text)
    if pm:
        poster = pm.group(1)
    if not poster:
        pm = re.search(r'class="[^"]*poster[^"]*"[^>]*src="([^"]+)"', text)
        if pm:
            poster = pm.group(1)
    
    # Description from og:description or meta description
    desc = ''
    dm = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', text)
    if dm:
        desc = dm.group(1)
    if not desc:
        dm = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', text)
        if dm:
            desc = dm.group(1)
    
    # Extract details from MasterSingleMeta section
    # Pattern: <span>LABEL : </span> <strong>VALUE</strong> or <a>VALUE</a>
    detail_labels = {
        'توقيت الفيلم': 'توقيت الفيلم :',
        'جودة الفيلم': 'جودة الفيلم :',
        'بطولة': 'بطولة :',
        'المخرجين': 'المخرجين :',
        'المؤلفين': 'المؤلفين :',
        'دولة الفيلم': 'دولة الفيلم :',
        'لغة الفيلم': 'لغة الفيلم :',
        'العمر': 'العمر :',
    }
    
    for label_key, label_text in detail_labels.items():
        m = re.search(r'<span>' + re.escape(label_text) + r'\s*</span>\s*<strong>([^<]+)</strong>', text)
        if m:
            details[label_key] = m.group(1).strip()
    
    # Cast (بطولة) - might be <a> tags instead of <strong>
    cast_m = re.search(r'<span>بطولة\s*:\s*</span>(.*?)</li>', text, re.DOTALL)
    if cast_m:
        cast_links = re.findall(r'<a[^>]*>([^<]+)</a>', cast_m.group(1))
        if cast_links:
            details['بطولة :'] = '، '.join(c.strip() for c in cast_links)
    
    # Director (المخرجين)
    dir_m = re.search(r'<span>المخرجين\s*:\s*</span>(.*?)</li>', text, re.DOTALL)
    if dir_m:
        dir_links = re.findall(r'<a[^>]*>([^<]+)</a>', dir_m.group(1))
        if dir_links:
            details['المخرجين :'] = '، '.join(d.strip() for d in dir_links)
    
    # Categories (deduplicated)
    cats = []
    seen_cats = set()
    breadcrumb = re.findall(r'<a[^>]*href="[^"]*category[^"]*"[^>]*>([^<]+)</a>', text)
    for c in breadcrumb:
        c = c.strip()
        if c and c not in ('الرئيسية', 'الأفلام', 'جميع الافلام', 'الحلقات', 'جميع الحلقات') and c not in seen_cats:
            cats.append(c)
            seen_cats.add(c)
    
    return {
        'watch_urls': watch_urls,
        'dl_links': dl_links,
        'server_name': si[0].strip() if si else 'TukTuk Vip',
        'poster': poster,
        'desc': desc,
        'details': details,
        'categories': cats,
    }

def extract(m):
    try:
        r = requests.get(m['url'], timeout=20, headers=headers)
        info = extract_details(r.text)
        if not info['watch_urls']:
            return {'title': m['name'], 'success': False}
        
        # Build output in same format as results_foreign.json
        titre = 'فيلم {} {} مترجم اون لاين'.format(m['name'], m['year'])
        video_url = info['watch_urls'][0]
        
        watch_servers = []
        for i, wu in enumerate(info['watch_urls']):
            sname = info['server_name'] if i == 0 else 'TukTuk {}'.format(i + 1)
            watch_servers.append({
                'name': sname,
                'url': wu,
                'isDefault': i == 0
            })
        
        download_servers = []
        for dl in info['dl_links']:
            download_servers.append({
                'name': 'Download',
                'url': dl
            })
        
        # Build details dict with the same keys as foreign format
        det = info['details']
        details_dict = {}
        if 'توقيت الفيلم' in det and det['توقيت الفيلم'].strip():
            details_dict['توقيت الفيلم :'] = det['توقيت الفيلم'].strip()
        if 'جودة الفيلم' in det and det['جودة الفيلم'].strip():
            details_dict['جودة الفيلم :'] = det['جودة الفيلم'].strip()
        if 'بطولة :' in det:
            details_dict['بطولة :'] = det['بطولة :']
        if 'المخرجين :' in det:
            details_dict['المخرجين :'] = det['المخرجين :']
        details_dict['موعد الصدور :'] = m['year']
        
        return {
            'titre': titre,
            'image': info['poster'],
            'video_url': video_url,
            'servers': {
                'watch': watch_servers,
                'download': download_servers
            },
            'info': {
                'story': info['desc'],
                'catssection': info['categories'],
                'details': details_dict
            },
            'success': True
        }
    except Exception as e:
        return {'title': m['name'], 'success': False}

print('Visiting {} pages...'.format(len(new_movies)))
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    futures = [ex.submit(extract, m) for m in new_movies]
    for i, future in enumerate(concurrent.futures.as_completed(futures)):
        results.append(future.result())
        if (i + 1) % 20 == 0 or i + 1 == len(new_movies):
            print('  {}/{}'.format(i + 1, len(new_movies)))

successful = [r for r in results if r.get('success')]
failed = [r for r in results if not r.get('success')]
print('Success: {}, Failed: {}'.format(len(successful), len(failed)))

# Remove success flag before saving
output = []
for r in successful:
    entry = {k: v for k, v in r.items() if k != 'success'}
    output.append(entry)

out_file = 'scripts/tuktukhd/data/results_asian.json'
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print('\nSaved {} movies to {}'.format(len(output), out_file))
print('Format matches results_foreign.json (titre, image, video_url, servers, info)')
