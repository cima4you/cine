import requests, re, json, concurrent.futures, base64, sys

headers = {'User-Agent': 'Mozilla/5.0'}
FILM_PATTERN = r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+'
BASE_URL = 'https://tuktukhd.com/category/movies-2/'

# Category mapping from URL slug to type
CAT_LABEL_MAP = {
    'افلام اجنبي': 'أجنبي',
    'افلام هندي': 'هندي',
    'افلام اسيوي': 'أسيوي',
    'افلام تركي': 'تركي',
    'افلام مدبلجة': 'مدبلج',
    'افلام انمي': 'أنمي',
}

PRIORITY = ['تركي', 'مدبلج', 'أنمي', 'نتفليكس', 'أسيوي', 'هندي', 'أجنبي']

def classify_from_catssection(html):
    cs = re.search(r'class="catssection"[^>]*>(.*?)</section>', html, re.DOTALL)
    if not cs:
        cs = re.search(r'<span>التصنيفات</span>(.*?)</li>', html, re.DOTALL)
    if not cs:
        return 'أجنبي'
    content = cs.group(1)
    cat_labels = re.findall(r'<a[^>]*>([^<]+)</a>', content)
    found_types = set()
    # Check for Netflix channel
    if 'film-netflix' in content:
        found_types.add('نتفليكس')
    for label in cat_labels:
        label = label.strip()
        if label in CAT_LABEL_MAP:
            found_types.add(CAT_LABEL_MAP[label])
    if not found_types:
        return 'أجنبي'
    for p in PRIORITY:
        if p in found_types:
            return p
    return 'أجنبي'

# Parse args
start_page = 1
end_page = 1
for arg in sys.argv[1:]:
    if arg.startswith('start='):
        start_page = int(arg.split('=')[1])
    elif arg.startswith('end='):
        end_page = int(arg.split('=')[1])

# Phase 1: Scrape listing pages
print('=== Phase 1: Scraping pages {}-{} ==='.format(start_page, end_page))
all_listings = []
for page in range(start_page, end_page + 1):
    url = '{}page/{}/'.format(BASE_URL, page) if page > 1 else BASE_URL
    try:
        r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        text = r.content.decode('utf-8')
        hrefs = re.findall(FILM_PATTERN, text, re.IGNORECASE)
        alts = re.findall(r'alt="([^"]+)"', text)
        page_movies = []
        for alt, href in zip(alts[:len(hrefs)], hrefs):
            alt = alt.strip()
            if alt == 'توك توك سينما':
                continue
            m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+(?:مترجم|مدبلج)', alt)
            if m:
                page_movies.append({'name': m.group(1).strip(), 'year': m.group(2), 'url': href})
        print('  page {}: {} movies'.format(page, len(page_movies)))
        all_listings.extend(page_movies)
        if len(page_movies) == 0:
            break
    except Exception as e:
        print('  page {} error: {}'.format(page, e))
        break

print('Total listings: {}'.format(len(all_listings)))

# Phase 2: Extract details & classify
print('\n=== Phase 2: Extracting details ===')
def extract(m):
    try:
        r = requests.get(m['url'], timeout=20, headers=headers)
        html = r.content.decode('utf-8')
        
        # Check if it's a series (has seasons structure)
        if re.search(r'class="[^"]*seasons[^"]*"', html) or re.search(r'class="[^"]*episodes[^"]*"', html):
            return None
        
        # Extract server data
        crypts = re.findall(r'data-crypt="([^"]+)"', html)
        watch_urls = []
        for c in crypts:
            try:
                watch_urls.append(base64.b64decode(c).decode('utf-8'))
            except:
                pass
        if not watch_urls:
            return None
        dl_links = re.findall(r'data-real-url="([^"]+)"', html)
        si = re.findall(r'<li[^>]*class="[^"]*server--item[^"]*"[^>]*>.*?<span>([^<]*)</span>', html, re.DOTALL)
        poster = ''
        pm = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
        if pm:
            poster = pm.group(1)
        if not poster:
            pm = re.search(r'class="[^"]*poster[^"]*"[^>]*src="([^"]+)"', html)
            if pm:
                poster = pm.group(1)
        desc = ''
        dm = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html)
        if dm:
            desc = dm.group(1)
        if not desc:
            dm = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html)
            if dm:
                desc = dm.group(1)
        details = {}
        for lt in ['توقيت الفيلم :', 'جودة الفيلم :', 'دولة الفيلم :', 'لغة الفيلم :', 'العمر :']:
            det_m = re.search(r'<span>' + re.escape(lt) + r'\s*</span>\s*<strong>([^<]+)</strong>', html)
            if det_m:
                details[lt] = det_m.group(1).strip()
        cast_m = re.search(r'<span>بطولة\s*:\s*</span>(.*?)</li>', html, re.DOTALL)
        if cast_m:
            cast_links = re.findall(r'<a[^>]*>([^<]+)</a>', cast_m.group(1))
            if cast_links:
                details['بطولة :'] = '، '.join(c.strip() for c in cast_links)
        dir_m = re.search(r'<span>المخرجين\s*:\s*</span>(.*?)</li>', html, re.DOTALL)
        if dir_m:
            dir_links = re.findall(r'<a[^>]*>([^<]+)</a>', dir_m.group(1))
            if dir_links:
                details['المخرجين :'] = '، '.join(d.strip() for d in dir_links)
        
        # Classify from catssection
        detected_type = classify_from_catssection(html)
        
        # Get categories from catssection for display
        cats_in_page = []
        cs = re.search(r'class="catssection"[^>]*>(.*?)</section>', html, re.DOTALL)
        if cs:
            cat_links = re.findall(r'<a[^>]*href="([^"]*category[^"]*)"[^>]*>([^<]+)</a>', cs.group(1))
            for _, label in cat_links:
                cats_in_page.append(label.strip())
        
        titre = 'فيلم {} {} مترجم اون لاين'.format(m['name'], m['year'])
        watch_servers = []
        for i, wu in enumerate(watch_urls):
            sname = si[i].strip() if i < len(si) else ('TukTuk Vip' if i == 0 else 'TukTuk {}'.format(i + 1))
            watch_servers.append({'name': sname, 'url': wu, 'isDefault': i == 0})
        download_servers = [{'name': 'Download', 'url': dl} for dl in dl_links]
        details_dict = {}
        for k in ['توقيت الفيلم :', 'جودة الفيلم :', 'بطولة :', 'المخرجين :', 'دولة الفيلم :', 'لغة الفيلم :']:
            v = details.get(k, '')
            if v and v.strip():
                details_dict[k] = v.strip()
        details_dict['موعد الصدور :'] = m['year']
        
        return {
            'titre': titre,
            'image': poster,
            'video_url': watch_servers[0]['url'],
            'servers': {'watch': watch_servers, 'download': download_servers},
            'info': {'story': desc, 'catssection': cats_in_page, 'details': details_dict},
            'type': detected_type,
        }
    except Exception:
        return None

results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    futures = [ex.submit(extract, m) for m in all_listings]
    for i, future in enumerate(concurrent.futures.as_completed(futures)):
        r = future.result()
        if r:
            results.append(r)
        if (i + 1) % 50 == 0 or i + 1 == len(all_listings):
            print('  {}/{} (success: {})'.format(i + 1, len(all_listings), len(results)))

# Save by type
print('\n=== Phase 3: Saving ===')
by_type = {}
for r in results:
    t = r.pop('type', 'أجنبي')
    by_type.setdefault(t, []).append(r)

output_dir = 'scripts/tuktukhd/data'
total = 0
for t, items in sorted(by_type.items()):
    fn = '{}/results_master_{}.json'.format(output_dir, t)
    with open(fn, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print('  {}: {}'.format(t, len(items)))
    total += len(items)

# Save combined
with open('{}/results_master_all.json'.format(output_dir), 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print('Total: {} saved to {}/'.format(total, output_dir))
print('\nUsage: python scrape_master.py start=1 end=10')
