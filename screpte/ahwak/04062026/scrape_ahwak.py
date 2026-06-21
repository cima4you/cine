import json, os, re, sys, time, threading
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
import requests, urllib3
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

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--cat', default='moslslat-ramadan-2024')
    parser.add_argument('--start', type=int, default=1)
    parser.add_argument('--end', type=int, default=None)
    parser.add_argument('--workers', type=int, default=5)
    args = parser.parse_args()
    
    # Auto-detect total pages
    if args.end is None:
        html = fetch(BASE + '/category.php?cat=' + args.cat)
        pages = re.findall(r'[?&]page=(\d+)', html)
        args.end = max(int(p) for p in pages) if pages else 1
        print('=== Auto-detected %d pages for %s ===' % (args.end, args.cat))
    
    all_eps = scrape_cat(args.cat, args.start, args.end, args.workers)
    print('\nTotal unique vids: %d' % len(all_eps))
    
    vids_list = list(all_eps.items())
    
    # Group by series
    series_map = {}
    for vid, (title, page) in vids_list:
        series, ep_num, prefix = parse_series_ep(title)
        if series not in series_map:
            series_map[series] = {'vids': {}, 'prefix': prefix}
        series_map[series]['vids'][vid] = ep_num
    
    print('Found %d unique series' % len(series_map))
    
    # Scrape metadata for each series (first episode)
    series_meta = {}
    meta_vids = {}
    for sname, sinfo in series_map.items():
        first_vid = next(iter(sinfo['vids'].keys()))
        meta_vids[first_vid] = sname
    
    def scrape_meta(vid, sname):
        try:
            ep_data = scrape_episode_data(vid)
            return sname, ep_data.get('meta', {})
        except:
            return sname, {}
    
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(scrape_meta, vid, sname): sname for vid, sname in meta_vids.items()}
        done = 0
        for fut in as_completed(futures):
            sname, meta = fut.result()
            series_meta[sname] = meta
            done += 1
            if done % 10 == 0:
                print('  Meta: %d/%d' % (done, len(meta_vids)))
    
    # Scrape servers for all vids
    all_vids = list(set(vid for vid, _ in all_eps.items()))
    total = len(all_vids)
    server_results = {}
    
    def scrape_vid(vid):
        html = fetch(BASE + '/see.php?vid=' + vid)
        if html:
            return vid, parse_see_page_servers(html)
        return vid, []
    
    with ThreadPoolExecutor(max_workers=min(args.workers, 3)) as ex:
        futures = {ex.submit(scrape_vid, vid): vid for vid in all_vids}
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
    
    # Build output
    output = []
    for sname, sinfo in sorted(series_map.items()):
        meta = series_meta.get(sname, {})
        cats = meta.get('categories', [])
        if not cats:
            cats = [args.cat.replace('-', ' ')]
        
        series_item = {
            'title': sname,
            'year': meta.get('year') or args.cat[-4:],
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
            servers = server_results.get(vid, [])
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
    
    # Stats
    total_eps = sum(len(s['seasons'][0]['episodes']) for s in output)
    total_servers = sum(1 for s in output for ep in s['seasons'][0]['episodes'] for _ in ep['servers'])
    print('\nSeries: %d, Episodes: %d, Servers: %d' % (len(output), total_eps, total_servers))
    
    safe_cat = args.cat.replace('-', '_')
    outpath = os.path.join(BASE_DIR, 'results_yam_%s.json' % safe_cat)
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print('Saved to %s' % outpath)

if __name__ == '__main__':
    main()
