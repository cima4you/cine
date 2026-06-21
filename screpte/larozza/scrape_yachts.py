#!/usr/bin/env python3
"""
Scraper for https://larozza.yachts
Scrapes category.php?cat=13-ramadan-2025 across all pages.
Structure: Category -> Series list -> Episodes -> Play page (servers)
Output: JSON file matching the data.js format.

Usage:
  python scrape_yachts.py [--cat 13-ramadan-2025] [--start 1] [--end 109] [--workers 5]
"""
import json, os, re, sys, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding='utf-8')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

BASE = 'https://larozza.yachts'
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

def parse_category_series(html):
    results = []
    for m in re.finditer(r'view-serie1\.php\?ser=([a-zA-Z0-9]+)"[^>]*>([^<]+)', html):
        ser = m.group(1)
        name = m.group(2).strip()
        results.append((ser, name))
    return results

def parse_episodes_from_series(html):
    eps = []
    seen = set()
    # Extract from <a> tags with text content
    for m in re.finditer(r'href="[^"]*video\.php\?vid=([a-f0-9]+)"[^>]*>([^<]*)</a>', html):
        vid = m.group(1)
        text = m.group(2).strip()
        if vid not in seen and text:
            seen.add(vid)
            eps.append((vid, text))
    # If few found, try <option> tags
    if len(eps) < 5:
        for m in re.finditer(r"value='video\.php\?vid=([a-f0-9]+)'[^>]*>([^<]+)", html):
            vid = m.group(1)
            text = m.group(2).strip()
            if vid not in seen and text:
                seen.add(vid)
                eps.append((vid, text))
    return eps

def parse_ep_num(title):
    m = re.search(r'الحلقة\s+(\d+)', title)
    if m:
        return int(m.group(1))
    return 0

def extract_series_name(title):
    t = title.strip()
    for prefix in ['مسلسل ', 'كرتون ', 'فيلم ', 'برنامج ']:
        if t.startswith(prefix):
            t = t[len(prefix):]
            break
    t = re.sub(r'\s+الحلقة\s+\d+.*$', '', t).strip()
    t = re.sub(r'\s+(HD|HQ|720p|1080p|بلوري|كام|DVD)\s*$', '', t, flags=re.I)
    return t

def parse_play_servers(html):
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

def extract_series_meta(video_html):
    meta = {'poster': '', 'description': '', 'categories': [], 'year': '2025'}
    m = re.search(r'og:image"\s+content="([^"]*)"', video_html)
    if m:
        meta['poster'] = m.group(1)
    m = re.search(r'og:description"\s+content="([^"]*)"', video_html)
    if m:
        meta['description'] = m.group(1)
    cat_section = re.search(r'video-category-line[^>]*>(.*?)(?:</div>|$)', video_html)
    if cat_section:
        for slug, name in re.findall(r'category\.php\?cat=([a-zA-Z0-9-]+)"[^>]*>([^<]+)', cat_section.group()):
            name = name.strip()
            if name and name not in meta['categories']:
                meta['categories'].append(name)
    return meta

def scrape_category_page(page, cat):
    url = BASE + '/category.php?cat=' + cat + '&page=' + str(page) + '&order=DESC'
    html = fetch(url)
    if not html:
        return page, []
    return page, parse_category_series(html)

def scrape_series_episodes(ser):
    """Scrape a series page to get all episodes."""
    html = fetch(BASE + '/view-serie1.php?ser=' + ser)
    if not html:
        return ser, [], {}
    eps = parse_episodes_from_series(html)
    # Also try to get series metadata from <p> with story or description
    meta = {'poster': '', 'description': '', 'categories': [], 'year': '2025'}
    m = re.search(r'<p[^>]*>(.*?)</p>', html[html.find('story'):html.find('story')+2000] if 'story' in html else '')
    # Poster from first video thumbnail
    poster_m = re.search(r'data-echo="([^"]*)"', html)
    if poster_m:
        meta['poster'] = poster_m.group(1).replace(' ', '%20')
    # Description from meta
    desc_m = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', html)
    if desc_m:
        meta['description'] = desc_m.group(1)
    return ser, eps, meta

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--cat', default='13-ramadan-2025')
    parser.add_argument('--start', type=int, default=1)
    parser.add_argument('--end', type=int, default=None)
    parser.add_argument('--workers', type=int, default=5)
    parser.add_argument('--max-series', type=int, default=0)
    args = parser.parse_args()

    if args.end is None:
        html = fetch(BASE + '/category.php?cat=' + args.cat + '&order=DESC')
        pages = re.findall(r'\?cat=[^"]*page=(\d+)', html)
        nums = [int(p) for p in pages if p.isdigit()]
        args.end = max(nums) if nums else 1
        print('=== Auto-detected %d pages for %s ===' % (args.end, args.cat))

    # Step 1: Collect all series from category pages
    all_series = {}
    print('Scraping category pages %d-%d...' % (args.start, args.end))
    with ThreadPoolExecutor(max_workers=min(args.workers, 10)) as ex:
        futures = {ex.submit(scrape_category_page, p, args.cat): p for p in range(args.start, args.end + 1)}
        for fut in as_completed(futures):
            page, series_list = fut.result()
            if not series_list:
                continue
            added = 0
            for ser, name in series_list:
                if ser not in all_series:
                    all_series[ser] = name
                    added += 1
            if page % 10 == 0 or page == args.end:
                print('  Page %d: +%d new, total: %d' % (page, added, len(all_series)))

    print('\nTotal unique series: %d' % len(all_series))

    if args.max_series and len(all_series) > args.max_series:
        all_series = dict(list(all_series.items())[:args.max_series])
        print('Limited to %d series' % len(all_series))

    # Step 2: Scrape episodes for each series
    series_vids = {}
    series_meta = {}
    print('Scraping series pages...')
    with ThreadPoolExecutor(max_workers=min(args.workers, 10)) as ex:
        futures = {ex.submit(scrape_series_episodes, ser): ser for ser in all_series}
        done = 0
        for fut in as_completed(futures):
            ser, eps, meta = fut.result()
            if eps:
                series_vids[ser] = eps
            series_meta[ser] = meta
            done += 1
            if done % 10 == 0 or done == len(all_series):
                total_eps = sum(len(v) for v in series_vids.values())
                print('  Series: %d/%d, episodes: %d' % (done, len(all_series), total_eps))

    # Step 3: Collect all vids and scrape servers
    all_vids = list(set(vid for eps in series_vids.values() for vid, _ in eps))
    print('\nTotal unique vids: %d' % len(all_vids))

    server_results = {}
    with ThreadPoolExecutor(max_workers=min(args.workers, 3)) as ex:
        def scrape_vid(vid):
            html = fetch(BASE + '/play.php?vid=' + vid)
            if html:
                return vid, parse_play_servers(html)
            return vid, []
        futures = {ex.submit(scrape_vid, vid): vid for vid in all_vids}
        done = 0
        for fut in as_completed(futures):
            try:
                vid, servers = fut.result(timeout=60)
                server_results[vid] = servers
            except:
                pass
            done += 1
            if done % 50 == 0 or done == len(all_vids):
                with_s = sum(1 for v in server_results if server_results.get(v))
                print('  Servers: %d/%d, with data: %d' % (done, len(all_vids), with_s))

    # Step 4: Build output
    output = []
    for ser, sname in sorted(all_series.items(), key=lambda x: x[1]):
        eps = series_vids.get(ser, [])
        if not eps:
            continue
        meta = series_meta.get(ser, {})
        cats = meta.get('categories', [args.cat.replace('-', ' ')])

        # Determine type based on series name
        stype = 'عربي'
        if 'تركي' in sname or any(k in sname for k in ['turk', 'ترك']):
            stype = 'تركي'

        series_item = {
            'title': sname,
            'year': meta.get('year', '2025'),
            'rating': '',
            'type': stype,
            'contentType': 'series',
            'description': meta.get('description', ''),
            'cast': [],
            'poster': meta.get('poster', ''),
            'categories': cats if cats else [args.cat.replace('-', ' ')],
            'quality': 'متعدد',
            'seasons': [{
                'seasonNumber': 1,
                'trial': '',
                'description': '',
                'poster': '',
                'episodes': []
            }]
        }

        ep_items = []
        for vid, title in eps:
            servers = server_results.get(vid, [])
            if not servers:
                continue
            ep_num = parse_ep_num(title)
            ep_items.append({
                'episodeNumber': ep_num,
                'title': 'حلقة %d' % ep_num if ep_num else title,
                'duration': '',
                'servers': servers,
                'downloadServers': []
            })

        ep_items.sort(key=lambda x: x['episodeNumber'])
        series_item['seasons'][0]['episodes'] = ep_items
        output.append(series_item)

    total_eps = sum(len(s['seasons'][0]['episodes']) for s in output)
    total_servers = sum(1 for s in output for ep in s['seasons'][0]['episodes'] for _ in ep['servers'])
    print('\nSeries: %d, Episodes: %d, Servers: %d' % (len(output), total_eps, total_servers))

    safe_cat = args.cat.replace('-', '_')
    outpath = os.path.join(DATA_DIR, 'results_yachts_%s.json' % safe_cat)
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print('Saved to %s' % outpath)

if __name__ == '__main__':
    main()
