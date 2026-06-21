import sys, json, requests, re, os, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(BASE_DIR, exist_ok=True)

BASE = 'https://yam.ahwaktv.net'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
}
import urllib3
urllib3.disable_warnings()

cookie_jar = None
cookie_lock = threading.Lock()
_thread_local = threading.local()

def init_session():
    sess = requests.Session()
    sess.headers.update(HEADERS)
    sess.verify = False
    resp = sess.get(BASE + '/', timeout=30)
    global cookie_jar
    with cookie_lock:
        if cookie_jar is None:
            cookie_jar = list(sess.cookies)
    for c in cookie_jar:
        sess.cookies.set(c.name, c.value)
    return sess

def get_session():
    if not hasattr(_thread_local, 'sess'):
        _thread_local.sess = init_session()
    return _thread_local.sess

def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            sess = get_session()
            resp = sess.get(url, timeout=30)
            if resp.status_code == 200 and 'Refresh' not in resp.text[:500]:
                return resp.text
            elif attempt == retries - 1:
                return None
            time.sleep(1)
        except:
            if attempt == retries - 1:
                return None
            time.sleep(1)
    return None

def parse_category(html):
    results = []
    for m in re.finditer(r'watch\.php\?vid=([a-f0-9]+)"\s*title="([^"]*)"', html):
        vid = m.group(1)
        title = m.group(2).strip()
        results.append((vid, title))
    return results

def parse_series_ep(title):
    t = title.strip()
    prefix = ''
    for p in ['مسلسل ', 'كرتون ', 'فيلم ', 'برنامج ']:
        if t.startswith(p):
            prefix = p.strip()
            t = t[len(p):]
            break
    t = re.sub(r'\s+(HD|HQ|720p|1080p|بلوري|كام|DVD)\s*$', '', t, flags=re.I)
    m = re.search(r'\s*الحلقة\s+(\d+)', t)
    ep_num = None
    if m:
        ep_num = int(m.group(1))
        t = t[:m.start()]
    return t.strip(), ep_num, prefix

def parse_see_page_servers(html):
    servers = []
    vidspeed = None
    idx = 0
    for m in re.finditer(r'data-embed-url="([^"]*)"', html):
        url = m.group(1)
        idx += 1
        if 'vidspeed' in url.lower():
            vidspeed = {'name': 'server%d' % idx, 'url': url, 'isDefault': True}
        else:
            servers.append({'name': 'server%d' % idx, 'url': url, 'isDefault': False})
    if vidspeed:
        servers.insert(0, vidspeed)
    for i, srv in enumerate(servers):
        srv['name'] = 'server%d' % (i+1)
        srv['isDefault'] = (i == 0)
    return servers

def extract_watch_meta(html, vid):
    meta = {'poster': '', 'description': '', 'categories': [], 'year': '', 'series_slug': ''}
    m = re.search(r'og:image"\s+content="([^"]*)"', html)
    if m:
        meta['poster'] = m.group(1)
    m = re.search(r'og:description"\s+content="([^"]*)"', html)
    if m:
        meta['description'] = m.group(1)
    cat_section = re.search(r'video-category-line[^>]*>(.*?)(?:</div>|$)', html)
    if cat_section:
        for slug, name in re.findall(r'category\.php\?cat=([a-zA-Z0-9-]+)"[^>]*>([^<]+)', cat_section.group()):
            name = name.strip()
            if name and name not in meta['categories']:
                meta['categories'].append(name)
    m = re.search(r'view-serie\.php\?ser=([^"]+)"', html)
    if m:
        meta['series_slug'] = m.group(1).strip()
    return meta

def scrape_episode_data(vid):
    result = {'vid': vid, 'series': '', 'ep_num': None, 'servers': [], 'title': ''}
    see_html = fetch(BASE + '/see.php?vid=' + vid)
    if see_html:
        result['servers'] = parse_see_page_servers(see_html)
    watch_html = fetch(BASE + '/watch.php?vid=' + vid)
    if watch_html:
        m = re.search(r'<title>([^<]*)</title>', watch_html)
        if m:
            result['title'] = m.group(1).strip()
        series, ep_num, prefix = parse_series_ep(result['title'])
        result['series'] = series
        result['ep_num'] = ep_num
        result['prefix'] = prefix
        meta = extract_watch_meta(watch_html, vid)
        result['meta'] = meta
    return result

def scrape_category_page(page, cat):
    url = BASE + '/category.php?cat=' + cat + '&page=' + str(page)
    html = fetch(url)
    if not html:
        return page, []
    return page, parse_category(html)

def scrape_cat(cat, start_page, end_page, workers=10):
    all_eps = {}
    print('Scraping pages %d-%d...' % (start_page, end_page))
    with ThreadPoolExecutor(max_workers=min(workers, 10)) as ex:
        futures = {ex.submit(scrape_category_page, p, cat): p for p in range(start_page, end_page + 1)}
        for fut in as_completed(futures):
            page, eps = fut.result()
            if not eps:
                continue
            added = 0
            for vid, title in eps:
                if vid not in all_eps:
                    all_eps[vid] = (title, page)
                    added += 1
            if page % 5 == 0 or page == end_page:
                print('  Page %d: +%d new, total: %d' % (page, added, len(all_eps)))
    return all_eps

cat = 'moslslat-ramadan-2024'

# Fix page detection
html = fetch(BASE + '/category.php?cat=' + cat)
pages = re.findall(r'[?&]page=(\d+)', html)
max_page = max(int(p) for p in pages) if pages else 1
print('=== Category: %s, Total pages: %d ===' % (cat, max_page))

all_eps = scrape_cat(cat, 1, max_page, workers=5)
print('\nTotal unique vids: %d' % len(all_eps))

vids_list = list(all_eps.items())

# Group by series using series_slug when possible
series_map = {}
vid_meta_cache = {}

for vid, (title, page) in vids_list:
    series, ep_num, prefix = parse_series_ep(title)
    
    # Try to get series_slug for this vid
    if vid not in vid_meta_cache:
        ep_data = scrape_episode_data(vid)
        vid_meta_cache[vid] = ep_data
    else:
        ep_data = vid_meta_cache[vid]
    
    slug = ep_data.get('meta', {}).get('series_slug', '') or series
    
    if slug not in series_map:
        series_map[slug] = {'vids': {}, 'prefix': prefix, 'title': series}
    series_map[slug]['vids'][vid] = ep_num

print('Found %d unique series' % len(series_map))

# Build series_meta from cache
series_meta = {}
for slug, sinfo in series_map.items():
    first_vid = next(iter(sinfo['vids'].keys()))
    meta = vid_meta_cache.get(first_vid, {}).get('meta', {})
    series_meta[slug] = meta

# Scrape servers for remaining vids that didn't get scraped
all_vids = list(set(vid for vid, _ in all_eps.items()))
remaining_vids = [v for v in all_vids if v not in vid_meta_cache or not vid_meta_cache[v].get('servers')]
total = len(remaining_vids)
server_results = {}

def scrape_vid(vid):
    html = fetch(BASE + '/see.php?vid=' + vid)
    if html:
        return vid, parse_see_page_servers(html)
    return vid, []

if remaining_vids:
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(scrape_vid, vid): vid for vid in remaining_vids}
        done = 0
        for fut in as_completed(futures):
            try:
                vid, servers = fut.result(timeout=60)
                server_results[vid] = servers
            except:
                pass
            done += 1
            if done % 50 == 0 or done == total:
                with_s = sum(1 for v in server_results if server_results.get(v))
                print('  Servers: %d/%d, with data: %d' % (done, total, with_s))

# Merge server_results into vid_meta_cache
for vid, servers in server_results.items():
    if vid in vid_meta_cache:
        vid_meta_cache[vid]['servers'] = servers

# Build output
output = []
for slug, sinfo in sorted(series_map.items()):
    meta = series_meta.get(slug, {})
    cats = meta.get('categories', [])
    if not cats:
        cats = [cat.replace('-', ' ')]

    series_item = {
        'title': sinfo['title'],
        'year': meta.get('year', cat[-4:]),
        'rating': '',
        'type': 'عربي',
        'contentType': 'series',
        'description': meta.get('description', ''),
        'cast': [],
        'poster': meta.get('poster', ''),
        'categories': cats,
        'quality': 'متعدد',
        'seasons': [{
            'seasonNumber': 1,
            'trial': '',
            'description': '',
            'poster': '',
            'episodes': []
        }]
    }

    eps = []
    for vid, ep_num in sinfo['vids'].items():
        if vid in vid_meta_cache:
            servers = vid_meta_cache[vid].get('servers', [])
        else:
            servers = []
        if not servers:
            continue
        eps.append({
            'episodeNumber': ep_num or 0,
            'title': 'حلقة %d' % ep_num if ep_num else 'حلقة',
            'duration': '',
            'servers': servers,
            'downloadServers': []
        })

    eps.sort(key=lambda x: x['episodeNumber'])
    series_item['seasons'][0]['episodes'] = eps
    output.append(series_item)

total_eps = sum(len(s['seasons'][0]['episodes']) for s in output)
total_servers = sum(1 for s in output for ep in s['seasons'][0]['episodes'] for _ in ep['servers'])
print('\nSeries: %d, Episodes: %d, Servers: %d' % (len(output), total_eps, total_servers))

safe_cat = cat.replace('-', '_')
outpath = os.path.join(BASE_DIR, 'results_yam_%s.json' % safe_cat)
with open(outpath, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print('Saved to %s' % outpath)
