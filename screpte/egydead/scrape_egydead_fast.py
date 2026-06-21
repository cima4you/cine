import undetected_chromedriver as uc
import requests, re, json, time, os, shutil, sys
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'scripts', 'egydead', 'data')
os.makedirs(OUTPUT_DIR, exist_ok=True)

BASE_URL = 'https://tv8.egydead.live'

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

CAT_LABEL_MAP = {
    'افلام اجنبي': 'أجنبي', 'افلام هندية': 'هندي', 'افلام هندي': 'هندي',
    'افلام اسيوية': 'أسيوي', 'افلام اسيوي': 'أسيوي',
    'افلام تركية': 'تركي', 'افلام تركي': 'تركي',
    'افلام اجنبية مدبلجة': 'مدبلج', 'افلام مدبلجة': 'مدبلج',
    'افلام كرتون': 'اطفال', 'افلام عربي': 'عربي',
    'افلام انمي': 'أنمي', 'افلام وثائقية': 'اخرى',
}

PRIORITY = ['تركي', 'مدبلج', 'أنمي', 'نتفليكس', 'أسيوي', 'هندي', 'أجنبي', 'عربي', 'اطفال', 'اخرى']

start_page = 1; end_page = 1; cat_slug = ''; max_movies = 0; workers = 5
for arg in sys.argv[1:]:
    if arg.startswith('start='): start_page = int(arg.split('=')[1])
    elif arg.startswith('end='): end_page = int(arg.split('=')[1])
    elif arg.startswith('cat='): cat_slug = arg.split('=')[1]
    elif arg.startswith('max='): max_movies = int(arg.split('=')[1])
    elif arg.startswith('workers='): workers = int(arg.split('=')[1])

cat_name = CATEGORIES.get(cat_slug, 'all')
print('=== Scraping EgyDead {} (pages {}-{}) workers={} ==='.format(cat_name, start_page, end_page, workers))


def get_cloudflare_session():
    """Selenium once -> get cookies -> return requests Session"""
    cache_dir = os.path.expanduser('~/.undetected_chromedriver')
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
    driver = uc.Chrome(headless=False, version_main=148)
    # Use a specific movie URL (solves faster than homepage)
    driver.get(BASE_URL)
    solved = False
    for i in range(60):
        time.sleep(1)
        title = driver.title
        src = driver.page_source
        if 'Un instant' not in title and 'Just a moment' not in title and 'challenge' not in src.lower()[:2000]:
            print('  Cloudflare solved after {}s'.format(i + 1))
            solved = True
            break
        if i % 5 == 0:
            print('  Cloudflare challenge... ({}) title={}'.format(i + 1, title))
    if not solved:
        print('  WARNING: Might not have solved Cloudflare, proceeding anyway...')
    time.sleep(2)
    cookies = driver.get_cookies()
    ua = driver.execute_script('return navigator.userAgent')
    driver.quit()

    s = requests.Session()
    s.headers.update({'User-Agent': ua})
    for c in cookies:
        s.cookies.set(c['name'], c['value'], domain=c.get('domain', ''))
    s.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
    })
    # Verify it works
    r = s.get(BASE_URL, timeout=15)
    if 'Just a moment' in r.text or 'challenge' in r.text:
        print('  WARNING: requests session blocked by Cloudflare!')
    else:
        print('  Session verified ({} KB)'.format(len(r.text) // 1024))
    return s


def scrape_listing(session, page_url):
    r = session.get(page_url, timeout=20)
    if 'Just a moment' in r.text:
        print('    Cloudflare blocked!')
        return []
    html = r.text
    items = re.findall(r'<li class="movieItem">(.*?)</li>', html, re.DOTALL)
    results = []
    for item_html in items:
        href_m = re.search(r'<a[^>]*href="([^"]+)"', item_html)
        title_m = re.search(r'<h1[^>]*class="[^"]*BottomTitle[^"]*"[^>]*>([^<]+)</h1>', item_html)
        img_m = re.search(r'<img[^>]*src="([^"]+)"', item_html)
        cat_m = re.search(r'<span[^>]*class="[^"]*cat_name[^"]*"[^>]*>([^<]+)</span>', item_html)
        label_m = re.search(r'<span[^>]*class="[^"]*label[^"]*"[^>]*>([^<]+)</span>', item_html)
        if href_m and title_m:
            results.append({
                'url': href_m.group(1) if href_m.group(1).startswith('http') else BASE_URL + href_m.group(1),
                'title': title_m.group(1).strip(),
                'image': img_m.group(1) if img_m else '',
                'category_name': cat_m.group(1).strip() if cat_m else '',
                'quality': label_m.group(1).strip() if label_m else '',
            })
    return results


def extract_type(cat_name_text):
    for label, t in CAT_LABEL_MAP.items():
        if label in cat_name_text:
            return t
    return 'أجنبي'


def extract_movie(session, movie):
    def fetch_page(url, post_data=None):
        try:
            if post_data:
                r = session.post(url, data=post_data, timeout=20)
            else:
                r = session.get(url, timeout=20)
            if 'Just a moment' in r.text or 'challenge' in r.text:
                return None
            return r.text
        except:
            return None

    html = fetch_page(movie['url'])
    if not html:
        return None

    try:
        # Basic info
        titre_m = re.search(r'<div class="singleTitle">\s*<span>\s*<em>([^<]+)</em>', html)
        titre = titre_m.group(1).strip() if titre_m else movie['title']

        poster = ''
        pm = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
        if pm: poster = pm.group(1)
        if not poster: poster = movie.get('image', '')

        # Story
        story = ''
        sm = re.search(r'<div class="extra-content">\s*<span>القصه</span>\s*<p>([^<]+)</p>', html, re.DOTALL)
        if sm: story = sm.group(1).strip()
        if not story:
            sm2 = re.search(r'<div class="singleStory">([^<]+)</div>', html)
            if sm2: story = sm2.group(1).strip()

        # Description
        description = ''
        dm = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html)
        if dm: description = dm.group(1)
        if not description:
            dm2 = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html)
            if dm2: description = dm2.group(1)

        # Details from LeftBox
        details = {}
        detail_section = re.search(r'<div class="LeftBox">\s*<ul>(.*?)</ul>', html, re.DOTALL)
        if detail_section:
            for li_html in re.findall(r'<li>(.*?)</li>', detail_section.group(1), re.DOTALL):
                span_m = re.search(r'<span>([^<]+)</span>', li_html)
                if not span_m: continue
                key = span_m.group(1).strip()
                links = re.findall(r'<a[^>]*>([^<]+)</a>', li_html)
                vals = [a.strip() for a in links if a.strip()]
                val = '، '.join(vals) if vals else ''
                if key and val and key not in details:
                    details[key] = val

        # Year
        year = details.get('السنه :', '')
        if not year:
            ym = re.search(r'(\d{4})', titre)
            if ym: year = ym.group(1)
        if year: details['السنه :'] = year

        # القسم from details (movie's actual category)
        sec_cats = []
        for k, v in details.items():
            if 'القسم' in k:
                sec_cats = [c.strip() for c in v.split('،') if c.strip()]

        # Breadcrumbs (first breadcrumb link after الرئيسيه)
        cat_labels = []
        bread_section = re.search(r'<div[^>]*class="[^"]*breadcrumbs-single[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        if bread_section:
            for m in re.finditer(r'<a[^>]*>([^<]+)</a>', bread_section.group(1)):
                txt = m.group(1).strip()
                if txt and txt != 'الرئيسيه':
                    cat_labels.append(txt)

        # Determine type: listing page name > القسم > first breadcrumb
        detected_type = extract_type(movie.get('category_name', ''))
        if detected_type == 'أجنبي' and sec_cats:
            for sc in sec_cats:
                t = extract_type(sc)
                if t != 'أجنبي': detected_type = t; break
        if detected_type == 'أجنبي' and cat_labels:
            t = extract_type(cat_labels[0])
            if t != 'أجنبي': detected_type = t

        # All categories: section + genres only (NO sidebar/footer links)
        all_cats = list(sec_cats)
        if cat_labels:
            for cl in cat_labels:
                if cl not in all_cats: all_cats.append(cl)
        genres_key = None
        for k in details:
            if 'النوع' in k: genres_key = k; break
        if genres_key:
            for gv in [g.strip() for g in details[genres_key].split('،')]:
                if gv not in all_cats: all_cats.append(gv)
        if not all_cats:
            all_cats = [CATEGORIES.get(cat_slug, 'افلام اجنبي')]

        # Cast
        cast_m = re.search(r'<div class="workTeam">\s*<ul>(.*?)</ul>', html, re.DOTALL)
        if cast_m:
            cast_names = re.findall(r'<a[^>]*>([^<]+)</a>', cast_m.group(1))
            if cast_names:
                details['بطولة :'] = '، '.join(c.strip() for c in cast_names)

        # Duration
        duration = details.get('مده العرض :', '')
        if duration:
            dd = re.search(r'(\d+)', duration)
            if dd: details['توقيت الفيلم :'] = dd.group(1) + ' min'

        ### Extract server data-link from HTML ###
        servers_watch = []
        data_links = re.findall(r'data-link="([^"]+)"', html)

        # If no data-links in GET, try POST with View=1
        if not data_links:
            html_post = fetch_page(movie['url'], {'View': '1'})
            if html_post:
                data_links = re.findall(r'data-link="([^"]+)"', html_post)
                if data_links:
                    html = html_post  # use POST html for further extraction too

        if data_links:
            server_names = re.findall(r'<li[^>]*data-link="[^"]*"[^>]*>\s*([^<]+?)\s*</li>', html, re.DOTALL)
            for idx, link in enumerate(data_links):
                name = server_names[idx].strip() if idx < len(server_names) and server_names[idx].strip() else 'Server {}'.format(idx + 1)
                servers_watch.append({
                    'name': name,
                    'url': link,
                    'isDefault': idx == 0,
                })
        else:
            iframes = re.findall(r'<iframe[^>]*src="([^"]+)"', html)
            for idx, src in enumerate(iframes[:5]):
                if src:
                    servers_watch.append({
                        'name': 'Server {}'.format(idx + 1),
                        'url': src,
                        'isDefault': idx == 0,
                    })

        video_url = servers_watch[0]['url'] if servers_watch else ''

        return {
            'titre': titre,
            'image': poster,
            'video_url': video_url,
            'servers': {'watch': servers_watch, 'download': []},
            'info': {
                'story': story or description,
                'catssection': all_cats,
                'details': details,
                '_detected_type': detected_type,
            },
        }
    except Exception as e:
        return None


# ==== MAIN ====
print('\n[1/3] Getting Cloudflare session...')
session = get_cloudflare_session()

print('\n[2/3] Scraping listings...')
all_listings = []
for page in range(start_page, end_page + 1):
    if cat_slug:
        page_url = '{}/category/{}/page/{}/'.format(BASE_URL, cat_slug, page) if page > 1 else '{}/category/{}/'.format(BASE_URL, cat_slug)
    else:
        page_url = '{}/page/{}/'.format(BASE_URL, page) if page > 1 else BASE_URL
    listings = scrape_listing(session, page_url)
    if not listings:
        print('  Page {}: 0 items (stopping)'.format(page))
        break
    all_listings.extend(listings)
    print('  Page {}: {} (total: {})'.format(page, len(listings), len(all_listings)))

if max_movies > 0:
    all_listings = all_listings[:max_movies]
print('  Total: {} movies'.format(len(all_listings)))

print('\n[3/3] Extracting details ({} workers)...'.format(workers))
results_by_type = {}
total_success = 0

with ThreadPoolExecutor(max_workers=workers) as ex:
    future_map = {ex.submit(extract_movie, session, m): i for i, m in enumerate(all_listings)}
    for future in as_completed(future_map):
        idx = future_map[future]
        movie = all_listings[idx]
        result = future.result()
        if result:
            detected_type = result['info'].pop('_detected_type', 'أجنبي')
            results_by_type.setdefault(detected_type, []).append(result)
            total_success += 1
            has_servers = bool(result.get('servers', {}).get('watch'))
            print('  [{}/{}] {:.50} {} {}'.format(idx + 1, len(all_listings), movie['title'], '✅' if has_servers else '⚠️', detected_type))
        else:
            print('  [{}/{}] {:.50} ❌'.format(idx + 1, len(all_listings), movie['title']))

# Save
print('\n=== Save Results ===')
for t, items in sorted(results_by_type.items()):
    fn = os.path.join(OUTPUT_DIR, 'results_egydead_{}.json'.format(t))
    with open(fn, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print('  {}: {} movies'.format(t, len(items)))

all_fn = os.path.join(OUTPUT_DIR, 'results_egydead_all.json')
all_items = []
for items in results_by_type.values(): all_items.extend(items)
with open(all_fn, 'w', encoding='utf-8') as f:
    json.dump(all_items, f, ensure_ascii=False, indent=2)
print('  All: {} movies'.format(len(all_items)))

print('\n=== Done: {}/{} ==='.format(total_success, len(all_listings)))
print('Types:', {t: len(v) for t, v in sorted(results_by_type.items())})
print('Usage: python scripts/egydead/scrape_egydead_fast.py cat=english-movies start=1 end=5 workers=10')
