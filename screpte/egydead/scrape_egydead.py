import cloudscraper, re, json, base64, concurrent.futures, sys, os

BASE_URL = 'https://tv8.egydead.live'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
scraper = cloudscraper.create_scraper()

CATEGORIES = {
    'english-movies': 'افلام اجنبي',
    'english-movies-dubbed': 'افلام اجنبية مدبلجة',
    'cartoon-movies': 'افلام كرتون',
    'asian-movies': 'افلام اسيوية',
    'indian-movies': 'افلام هندية',
    'turkish-movies': 'افلام تركية',
    'arabic-movies': 'افلام عربي',
    'anime-movies': 'افلام انمي',
    'documentary-movies': 'افلام وثائقية',
}

# Map category slug to our type
CAT_TYPE = {
    'english-movies': 'أجنبي',
    'english-movies-dubbed': 'مدبلج',
    'cartoon-movies': 'اطفال',
    'asian-movies': 'أسيوي',
    'indian-movies': 'هندي',
    'turkish-movies': 'تركي',
    'arabic-movies': 'عربي',
    'anime-movies': 'أنمي',
    'documentary-movies': 'وثائقي',
}

def scrape_listing(cat_slug, start_page, end_page):
    results = []
    for page in range(start_page, end_page + 1):
        if cat_slug:
            url = '{}/category/{}/page/{}/'.format(BASE_URL, cat_slug, page) if page > 1 else '{}/category/{}/'.format(BASE_URL, cat_slug)
        else:
            url = '{}/?page={}'.format(BASE_URL, page) if page > 1 else BASE_URL
        try:
            r = scraper.get(url, timeout=20, headers=HEADERS)
            html = r.text
            items = re.findall(r'<li class="movieItem">(.*?)</li>', html, re.DOTALL)
            page_results = []
            for item_html in items:
                href_m = re.search(r'<a[^>]*href="([^"]+)"', item_html)
                img_m = re.search(r'<img[^>]*src="([^"]+)"', item_html)
                title_m = re.search(r'<h1[^>]*class="[^"]*BottomTitle[^"]*"[^>]*>([^<]+)</h1>', item_html)
                cat_m = re.search(r'<span[^>]*class="[^"]*cat_name[^"]*"[^>]*>([^<]+)</span>', item_html)
                if href_m and title_m:
                    page_results.append({
                        'url': href_m.group(1) if href_m.group(1).startswith('http') else BASE_URL + href_m.group(1),
                        'title': title_m.group(1).strip(),
                        'image': img_m.group(1) if img_m else '',
                        'category_name': cat_m.group(1).strip() if cat_m else '',
                    })
            print('  page {}: {} items'.format(page, len(page_results)))
            results.extend(page_results)
            if len(page_results) == 0:
                break
        except Exception as e:
            print('  page {} error: {}'.format(page, e))
            break
    return results

def extract_details(movie):
    try:
        r = scraper.get(movie['url'], timeout=20, headers=HEADERS)
        html = r.text
        
        # Check for Cloudflare
        if 'Just a moment' in html or 'challenge' in html:
            return None
        
        # Look for video URLs
        crypts = re.findall(r'data-crypt="([^"]+)"', html)
        watch_urls = []
        for c in crypts:
            try:
                watch_urls.append(base64.b64decode(c).decode('utf-8'))
            except:
                pass
        
        # Look for iframes
        iframe_urls = re.findall(r'<iframe[^>]*src="([^"]+)"', html)
        
        # Look for download links
        dl_links = re.findall(r'data-real-url="([^"]+)"', html)
        
        # If no server data found, look for common patterns
        if not watch_urls and not iframe_urls:
            # Try to find video sources in script tags
            for script_m in re.finditer(r'<script[^>]*>(.*?)</script>', html, re.DOTALL):
                for url_m in re.finditer(r'https?://[^\s"\'<>]+\.(?:m3u8|mp4)[^\s"\'<>]*', script_m.group(1)):
                    if url_m:
                        iframe_urls.append(url_m.group())
        
        if not watch_urls and not iframe_urls:
            return None
        
        # Poster from og:image
        poster = ''
        pm = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
        if pm:
            poster = pm.group(1)
        if not poster:
            poster = movie.get('image', '')
        
        # Description
        desc = ''
        dm = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html)
        if dm:
            desc = dm.group(1)
        if not desc:
            dm = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html)
            if dm:
                desc = dm.group(1)
        
        # Extract details
        details = {}
        for lt in ['توقيت الفيلم :', 'جودة الفيلم :', 'دولة الفيلم :', 'لغة الفيلم :', 'العمر :']:
            m = re.search(r'<span>' + re.escape(lt) + r'\s*</span>\s*<strong>([^<]+)</strong>', html)
            if m:
                details[lt] = m.group(1).strip()
        
        # Cast and director
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
        
        # Year from title
        year_m = re.search(r'(\d{4})', movie['title'])
        year = year_m.group(1) if year_m else ''
        
        # Build servers
        all_watch = watch_urls + iframe_urls
        watch_servers = []
        for i, wu in enumerate(all_watch[:10]):
            watch_servers.append({'name': 'Server {}'.format(i + 1), 'url': wu, 'isDefault': i == 0})
        download_servers = [{'name': 'Download', 'url': dl} for dl in dl_links[:5]]
        
        # Get type from category
        detected_type = movie.get('type', 'أجنبي')
        
        titre = 'فيلم {} {} مترجم'.format(movie['title'], year) if year else 'فيلم {} مترجم'.format(movie['title'])
        
        return {
            'titre': titre,
            'image': poster,
            'video_url': all_watch[0] if all_watch else '',
            'servers': {'watch': watch_servers, 'download': download_servers},
            'info': {
                'story': desc,
                'catssection': [movie.get('category_name', '')],
                'details': details,
            },
            'type': detected_type,
        }
    except:
        return None

# Parse args
start_page = 1
end_page = 1
cat_slug = ''
for arg in sys.argv[1:]:
    if arg.startswith('start='):
        start_page = int(arg.split('=')[1])
    elif arg.startswith('end='):
        end_page = int(arg.split('=')[1])
    elif arg.startswith('cat='):
        cat_slug = arg.split('=')[1]

cat_name = CATEGORIES.get(cat_slug, 'all')
print('=== Scraping {} (pages {}-{}) ==='.format(cat_name, start_page, end_page))

listings = scrape_listing(cat_slug, start_page, end_page)
print('Total listings: {}'.format(len(listings)))

# Assign type
for m in listings:
    m['type'] = CAT_TYPE.get(cat_slug, 'أجنبي')

print('\n=== Extracting details ===')
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
    futures = [ex.submit(extract_details, m) for m in listings]
    for i, future in enumerate(concurrent.futures.as_completed(futures)):
        r = future.result()
        if r:
            results.append(r)
        if (i + 1) % 20 == 0 or i + 1 == len(listings):
            print('  {}/{} (success: {})'.format(i + 1, len(listings), len(results)))

# Save
output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts', 'egydead', 'data')
os.makedirs(output_dir, exist_ok=True)

by_type = {}
for r in results:
    t = r.pop('type', 'أجنبي')
    by_type.setdefault(t, []).append(r)

total = 0
for t, items in sorted(by_type.items()):
    fn = os.path.join(output_dir, 'results_egydead_{}.json'.format(t))
    with open(fn, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print('  {}: {}'.format(t, len(items)))
    total += len(items)

print('Total: {} movies'.format(total))
print('\nUsage: python scripts/egydead/scrape_egydead.py cat=english-movies start=1 end=5')
print('Categories:', ', '.join(CATEGORIES.keys()))
print('Or omit cat= for homepage (all latest)')
