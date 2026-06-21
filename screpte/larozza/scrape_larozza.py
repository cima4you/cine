#!/usr/bin/env python3
"""
Scraper for https://larozza.living
Scrapes category.php?cat=ramadan-2026 across all pages.
Extracts: series info, episodes, server URLs (from play.php), downloads.
Output: JSON file matching the data.js format.

Usage:
  python scrape_larozza.py [--cat ramadan-2026] [--start 1] [--end 115] [--workers 10]
"""
import json, os, re, sys, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding='utf-8')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

BASE = 'https://larozza.living'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
}

import requests
import urllib3
urllib3.disable_warnings()

from threading import local

cookie_jar = None
cookie_lock = threading.Lock()

def init_session():
    sess = requests.Session()
    sess.headers.update(HEADERS)
    sess.verify = False
    # Visit homepage for cookies
    resp = sess.get(BASE + '/', timeout=30)
    # Share cookies across sessions
    global cookie_jar
    with cookie_lock:
        if cookie_jar is None:
            cookie_jar = list(sess.cookies)
    # Apply shared cookies
    for c in cookie_jar:
        sess.cookies.set(c.name, c.value)
    return sess

_thread_sessions = local()

def get_session():
    if not hasattr(_thread_sessions, 'sess'):
        _thread_sessions.sess = init_session()
    return _thread_sessions.sess

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
        except Exception as e:
            if attempt == retries - 1:
                return None
            time.sleep(1)
    return None

def parse_category(html):
    """Extract (vid, title, duration) from a category page."""
    results = []
    for m in re.finditer(r'video\.php\?vid=([a-f0-9]+)"\s*title="([^"]*)"', html):
        vid = m.group(1)
        title = m.group(2)
        results.append((vid, title))
    return results

def parse_series_name_and_ep(title):
    """Parse 'مسلسل عين سحرية الحلقة 7 السابعة' -> ('عين سحرية', 7)"""
    title = title.strip()
    # Remove prefix
    series = title
    prefix = ''
    for p in ['مسلسل ', 'كرتون ', 'فيلم ', 'برنامج ']:
        if series.startswith(p):
            prefix = p.strip()
            series = series[len(p):]
            break
    # Remove ' الحلقة X' suffix
    m = re.search(r'\s*الحلقة\s+(\d+)', series)
    ep_num = None
    if m:
        ep_num = int(m.group(1))
        series = series[:m.start()]
    return series.strip(), ep_num, prefix

def extract_meta_from_video_page(html, vid):
    """Extract series metadata from a video.php page."""
    meta = {'poster': '', 'description': '', 'categories': [], 'year': '2026', 'series_slug': ''}
    
    m = re.search(r'<meta\s+property="og:image"\s+content="([^"]*)"', html)
    if m:
        meta['poster'] = m.group(1)
    
    m = re.search(r'<meta\s+(?:name|property)="description"\s+content="([^"]*)"', html)
    if not m:
        m = re.search(r'<meta\s+property="og:description"\s+content="([^"]*)"', html)
    if m:
        meta['description'] = m.group(1)
    
    # Extract categories from video info section only
    cat_section = re.search(r'video-category-line[^>]*>.*?(?:</div>|$)', html)
    if cat_section:
        cats = re.findall(r'category\.php\?cat=([a-zA-Z0-9-]+)"[^>]*>([^<]+)', cat_section.group())
        for slug, name in cats:
            name = name.strip()
            if name and name not in meta['categories']:
                meta['categories'].append(name)
    
    # Extract series slug from view-serie link
    m = re.search(r'view-serie\.php\?ser=([^"]+)"\s*title="([^"]*)"', html)
    if m:
        meta['series_slug'] = m.group(1)
    
    m = re.search(r'<meta\s+name="keywords"\s+content="([^"]*)"', html)
    if m:
        kw = m.group(1)
        yr = re.search(r'\b(202\d)\b', kw)
        if yr:
            meta['year'] = yr.group(1)
    
    return meta

def parse_play_page_servers(html):
    """Extract embed server URLs from play.php page."""
    servers = []
    vidspeed = None
    idx = 0
    for m in re.finditer(r'data-embed-url="([^"]*)"', html):
        url = m.group(1)
        idx += 1
        if 'vidspeed' in url.lower():
            vidspeed = {'name': f"server{idx}", 'url': url, 'isDefault': True}
        else:
            servers.append({'name': f"server{idx}", 'url': url, 'isDefault': False})
    if vidspeed:
        servers.insert(0, vidspeed)
    for i, srv in enumerate(servers):
        srv['name'] = f"server{i+1}"
        srv['isDefault'] = (i == 0)
    return servers

def parse_episode_nav(html):
    """Extract previous/next episode links from video page."""
    prev_vid = None
    next_vid = None
    m = re.search(r'href="[^"]*video\.php\?vid=([a-f0-9]+)"[^>]*class="[^"]*prev[^"]*"', html)
    if m:
        prev_vid = m.group(1)
    m = re.search(r'href="[^"]*video\.php\?vid=([a-f0-9]+)"[^>]*class="[^"]*next[^"]*"', html)
    if m:
        next_vid = m.group(1)
    return prev_vid, next_vid

def scrape_category_page(page, cat='ramadan-2026'):
    """Scrape a single category page and return (page_num, [(vid, title), ...])."""
    url = f'{BASE}/category.php?cat={cat}&page={page}'
    html = fetch(url)
    if not html:
        return page, []
    eps = parse_category(html)
    return page, eps

def scrape_episode(vid, known_series=None):
    """Scrape a single episode: metadata + servers."""
    result = {'vid': vid, 'series': '', 'ep_num': None, 'servers': [], 'title': ''}
    
    # Fetch play.php for servers
    play_html = fetch(f'{BASE}/play.php?vid={vid}')
    if play_html:
        result['servers'] = parse_play_page_servers(play_html)
    
    # Try to get episode title from video.php
    video_html = fetch(f'{BASE}/video.php?vid={vid}')
    if video_html:
        # Extract page title
        m = re.search(r'<title>([^<]*)</title>', video_html)
        if m:
            result['title'] = m.group(1)
        # Parse series+ep from title
        series, ep_num, prefix = parse_series_name_and_ep(result['title'])
        result['series'] = series
        result['ep_num'] = ep_num
        result['prefix'] = prefix
        
        # Get metadata if we need it for this series
        meta = extract_meta_from_video_page(video_html, vid)
        result['meta'] = meta
    
    return result

# ---- Main scraping logic ----

def scrape_category_range(cat, start, end, workers):
    """Scrape all category pages to collect episode URLs."""
    all_episodes = {}  # vid -> (title, page)
    print(f'Scraping category pages {start}-{end}...')
    
    with ThreadPoolExecutor(max_workers=min(workers, 10)) as executor:
        futures = {executor.submit(scrape_category_page, p, cat): p for p in range(start, end + 1)}
        for fut in as_completed(futures):
            page, eps = fut.result()
            if not eps:
                continue
            added = 0
            for vid, title in eps:
                if vid not in all_episodes:
                    all_episodes[vid] = (title, page)
                    added += 1
            if page % 10 == 0 or page == end:
                print(f'  Page {page}: +{added} new, total unique: {len(all_episodes)}')
    
    return all_episodes

def scrape_episode_servers(vids, workers):
    """Scrape play.php for each vid to get server URLs."""
    # First, get series grouping from titles
    series_map = {}
    for vid, title, page in vids:
        series, ep_num, prefix = parse_series_name_and_ep(title)
        if series not in series_map:
            series_map[series] = {'vids': {}, 'prefix': prefix, 'page': page}
        series_map[series]['vids'][vid] = ep_num
    
    print(f'Found {len(series_map)} unique series')
    
    # Scrape metadata for each series (first episode only)
    series_meta = {}
    meta_vids = {next(iter(sinfo['vids'].keys())): sname for sname, sinfo in series_map.items()}
    
    def scrape_meta(vid, sname):
        ep_data = scrape_episode(vid)
        return vid, sname, ep_data
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(scrape_meta, vid, sname): (vid, sname) for vid, sname in meta_vids.items()}
        done = 0
        for fut in as_completed(futures):
            vid, sname, ep_data = fut.result()
            series_meta[sname] = ep_data.get('meta', {})
            done += 1
            if done % 10 == 0:
                print(f'  Meta: {done}/{len(meta_vids)}')
    
    # Scrape servers for all vids
    results = {}
    total = len(vids)
    
    def scrape_vid_servers(vid):
        play_html = fetch(f'{BASE}/play.php?vid={vid}')
        if not play_html:
            return vid, []
        servers = parse_play_page_servers(play_html)
        if not servers:
            time.sleep(0.5)  # retry once if empty
            play_html = fetch(f'{BASE}/play.php?vid={vid}')
            if play_html:
                servers = parse_play_page_servers(play_html)
        return vid, servers
    
    # Scrape servers
    vids_list = list(set(vid for vid, _, _ in vids))
    total = len(vids_list)
    print(f'  Scraping {total} unique vids for servers...')
    
    def scrape_vid(vid):
        html = fetch(f'{BASE}/play.php?vid={vid}')
        if html:
            return vid, parse_play_page_servers(html)
        return vid, []
    
    with ThreadPoolExecutor(max_workers=min(workers, 3)) as ex:
        futures = {ex.submit(scrape_vid, vid): vid for vid in vids_list}
        done = 0
        for fut in as_completed(futures):
            try:
                vid, servers = fut.result(timeout=60)
                results[vid] = servers
            except Exception:
                pass
            done += 1
            if done % 50 == 0 or done == total:
                with_s = sum(1 for v in results if results.get(v))
                print(f'  Servers: {done}/{total}, with data: {with_s}')
    
    print(f'  Server results: {len(results)} vids, sample: {list(results.keys())[:5]}')
    return series_map, series_meta, results


def build_output(series_map, series_meta, server_results, cat='ramadan-2026'):
    """Build the final output JSON in data.js format."""
    output = []
    
    for sname, sinfo in sorted(series_map.items()):
        meta = series_meta.get(sname, {})
        prefix = sinfo.get('prefix', '')
        
        cat_names = meta.get('categories', [cat])
        if not cat_names:
            cat_names = [{'ramadan-2026': 'مسلسلات رمضان 2026'}.get(cat, cat)]
        
        series_item = {
            'title': sname,
            'year': meta.get('year', '2026'),
            'rating': '',
            'type': 'عربي',
            'contentType': 'series',
            'description': meta.get('description', ''),
            'cast': [],
            'poster': meta.get('poster', ''),
            'categories': cat_names,
            'quality': 'متعدد',
            'seasons': [{
                'seasonNumber': 1,
                'trial': '',
                'description': '',
                'poster': '',
                'episodes': []
            }]
        }
        
        # Collect all episodes for this series, sorted by ep number
        episodes_data = []
        for vid, ep_num in sinfo['vids'].items():
            servers = server_results.get(vid, [])
            if not servers or not isinstance(servers, list) or len(servers) == 0:
                continue
            ep_title = f'حلقة {ep_num}' if ep_num else f'حلقة'
            ep_item = {
                'episodeNumber': ep_num or 0,
                'title': ep_title,
                'duration': '',
                'servers': servers,
                'downloadServers': []
            }
            episodes_data.append(ep_item)
        
        episodes_data.sort(key=lambda x: x['episodeNumber'])
        series_item['seasons'][0]['episodes'] = episodes_data
        output.append(series_item)
    
    return output


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--cat', default='ramadan-2026')
    parser.add_argument('--start', type=int, default=1)
    parser.add_argument('--end', type=int, default=115)
    parser.add_argument('--workers', type=int, default=10)
    args = parser.parse_args()
    
    print(f'=== Scraping category: {args.cat} ===')
    
    # Step 1: Collect all vids from category pages
    all_eps = scrape_category_range(args.cat, args.start, args.end, args.workers)
    print(f'\nTotal unique episodes: {len(all_eps)}')
    
    vids_list = [(vid, title, page) for vid, (title, page) in all_eps.items()]
    
    # Step 2: Scrape servers
    series_map, series_meta, server_results = scrape_episode_servers(vids_list, args.workers)
    
    # Step 3: Build output
    output = build_output(series_map, series_meta, server_results, args.cat)
    
    total_eps = sum(len(s['seasons'][0]['episodes']) for s in output)
    total_servers = sum(1 for s in output for ep in s['seasons'][0]['episodes'] for _ in ep['servers'])
    print(f'\nSeries: {len(output)}, Episodes: {total_eps}, Servers: {total_servers}')
    
    # Save
    safe_cat = args.cat.replace('-', '_')
    outpath = os.path.join(DATA_DIR, f'results_larozza_{safe_cat}.json')
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f'Saved {len(output)} series to {outpath}')
