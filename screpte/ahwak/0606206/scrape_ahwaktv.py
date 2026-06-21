#!/usr/bin/env python3
"""
AhwakTV Scraper - Turkish Series
=================================
Scrapes https://yam.ahwaktv.net for Turkish series metadata, episodes, and video embeds.

Usage:
  python scrape_ahwaktv.py --start 1 --end 5 --max-series 10
  python scrape_ahwaktv.py --start 1 --end 2 --max-series 5 --episodes-only

Options:
  --start PAGE         First category page (default: 1)
  --end PAGE           Last category page (default: 1)
  --max-series N       Max number of series to process (default: 10)
  --episodes-only      Only collect episode links, skip embed extraction
  --output FILE        Output file (default: ahwaktv_data.json)
  --debug              Save debug HTML files
"""

import sys, time, json, os, re, argparse, base64, math
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

import undetected_chromedriver as uc

BASE_URL = 'https://yam.ahwaktv.net'
CATEGORY_URL = BASE_URL + '/category.php?cat=moslslat-turkiaa-motrgma'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def eta_str(current, total, start_time):
    if current == 0:
        return '--:--:-- remaining'
    elapsed = time.time() - start_time
    per_item = elapsed / current
    remaining = per_item * (total - current)
    return f'{format_time(remaining)} remaining'

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f'{h}h{m:02d}m{s:02d}s'
    elif m > 0:
        return f'{m}m{s:02d}s'
    else:
        return f'{s}s'

def progress_bar(current, total, start_time, width=20):
    if total == 0:
        return '[--]'
    done = int(width * current / total)
    bar = '█' * done + '░' * (width - done)
    pct = int(100 * current / total)
    eta = eta_str(current, total, start_time)
    return f'[{bar}] {pct}% {eta}'


def load_existing_data(output_path):
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def merge_series_data(existing, new_list):
    existing_by_url = {}
    existing_by_name = {}
    for s in existing:
        if s.get('series_url'):
            existing_by_url[s['series_url']] = s
        if s.get('name'):
            existing_by_name[s['name']] = s

    for new_s in new_list:
        match = None
        url = new_s.get('series_url', '')
        name = new_s.get('name', '')
        if url and url in existing_by_url:
            match = existing_by_url[url]
        elif name and name in existing_by_name:
            match = existing_by_name[name]

        if match:
            if new_s.get('poster'):
                match['poster'] = new_s['poster']
            if new_s.get('description'):
                match['description'] = new_s['description']
            existing_numbers = {e['number'] for e in match.get('episodes', [])}
            for ep in new_s.get('episodes', []):
                if ep['number'] not in existing_numbers:
                    match['episodes'].append(ep)
            match['episodes'].sort(key=lambda x: x['number'])
        else:
            existing.append(new_s)

    return existing


# ==================== PHASE 1: Discover series from category pages ====================

def parse_category_page(html):
    items = []
    for item_html in re.finditer(
        r'<li class="col-xs-6 col-sm-4 col-md-3">.*?<a href="[^"]*(watch\.php\?vid=[^"]+)"[^>]*title="([^"]*)"',
        html, re.DOTALL
    ):
        vid_url = item_html.group(1)
        title = item_html.group(2)
        thumb_m = re.search(r'<img[^>]*src="([^"]*)"[^>]*alt="[^"]*"', item_html.group(0))
        thumb = thumb_m.group(1) if thumb_m else ''
        full_url = vid_url if vid_url.startswith('http') else BASE_URL + '/' + vid_url
        items.append({'title': title, 'url': full_url, 'thumb': thumb})
    return items


def extract_series_name(ep_title):
    name = re.sub(r'\s+الحلقة\s+\d+.*$', '', ep_title)
    name = re.sub(r'\s+(مترجمة|مدبلجة|HD|720p|1080p)\s*$', '', name)
    name = re.sub(r'\s+(مترجم|مدبلج)\s*$', '', name)
    name = name.strip()
    if not name.startswith('مسلسل') and not name.startswith('الموسم'):
        name = 'مسلسل ' + name
    return name


def safe_driver_get(driver, url, max_retries=3, wait=8):
    for attempt in range(max_retries):
        try:
            driver.get(url)
            time.sleep(wait)
            return True
        except Exception as e:
            msg = str(e)
            if attempt < max_retries - 1:
                print(f'    RETRY {attempt+1}/{max_retries}: {msg[:60]}')
                time.sleep(5)
            else:
                print(f'    FAILED: {msg[:80]}')
                return False
    return False


def scrape_category_pages(drv, start_page, end_page, debug=False):
    all_episodes = []
    unique_series = {}
    consecutive_empty = 0
    start_time = time.time()
    total_pages = end_page - start_page + 1
    pages_since_restart = 0
    for page in range(start_page, end_page + 1):
        # Restart browser every 5 pages to avoid session death
        if pages_since_restart >= 5:
            print(f'    Restarting browser to prevent session crash...')
            try: drv.quit()
            except: pass
            drv = uc.Chrome(options=make_options(), version_main=148)
            drv.get(BASE_URL)
            time.sleep(15)
            pages_since_restart = 0
        pbar = progress_bar(page - start_page + 1, total_pages, start_time)
        url = f'{CATEGORY_URL}&page={page}&order=DESC'
        print(f'  Page {page} {pbar}: {url}')
        for attempt in range(3):
            try:
                if not safe_driver_get(drv, url):
                    raise Exception('get failed')
                time.sleep(3)
                html = drv.page_source
                break
            except Exception:
                if attempt < 2:
                    print(f'    Session dead, restarting browser (attempt {attempt+2}/3)...')
                    try: drv.quit()
                    except: pass
                    drv = uc.Chrome(options=make_options(), version_main=148)
                    drv.get(BASE_URL)
                    time.sleep(15)
                else:
                    print(f'    SKIP (after 3 attempts)')
                    html = ''
        if not html:
            consecutive_empty += 1
            if consecutive_empty >= 3:
                print(f'    Too many timeouts, stopping.')
                break
            continue
        consecutive_empty = 0
        pages_since_restart += 1
        if debug:
            with open(f'debug_ahwaktv_page{page}.html', 'w', encoding='utf-8') as f:
                f.write(html)
        items = parse_category_page(html)
        print(f'    Found {len(items)} items')
        if len(items) == 0:
            print(f'    Empty page, stopping pagination.')
            break
        for item in items:
            all_episodes.append(item)
            series_name = extract_series_name(item['title'])
            if series_name and series_name not in unique_series:
                unique_series[series_name] = {
                    'name': series_name,
                    'sample_vid': item['url'],
                    'sample_title': item['title'],
                    'thumb': item['thumb']
                }
    print(f'\nTotal episodes: {len(all_episodes)}')
    print(f'Unique series: {len(unique_series)}')
    return all_episodes, unique_series


# ==================== PHASE 2: Extract series details and episode lists ====================

def parse_episode_page(html):
    result = {}
    m = re.search(r'<div class="pm-series-brief">.*?<img[^>]*src="([^"]*)"', html, re.DOTALL)
    if m:
        result['poster'] = m.group(1)
    m = re.search(r'<h1 class="title">([^<]+)</h1>', html)
    if m:
        result['series_name'] = m.group(1).strip()
    else:
        # fallback: try to get series name from the breadcrumb / category link area
        m = re.search(r'view-serie\.php\?name=([^"\'&]+)', html)
        if m:
            name = m.group(1).replace('-', ' ').replace('+', ' ')
            import urllib.parse
            result['series_name'] = urllib.parse.unquote(name).strip()
    m = re.search(r'<div class="description">\s*<p>([^<]*)</p>', html, re.DOTALL)
    if m:
        result['description'] = m.group(1).strip()
    m = re.search(r'href=(["\'])[^"\']*(view-serie\.php\?name=[^"\']+)\1', html)
    if m:
        vid = m.group(2)
        result['series_url'] = vid if vid.startswith('http') else BASE_URL + '/' + vid
    episodes = []
    for m in re.finditer(
        r'<a[^>]*title=(["\'])([^"\']+)\1[^>]*href=(["\'])(watch\.php\?vid=[^"\']+)\3[^>]*><em>(\d+)</em>',
        html
    ):
        ep_title = m.group(2)
        ep_vid = m.group(4)
        ep_num = int(m.group(5))
        ep_url = BASE_URL + '/' + ep_vid if not ep_vid.startswith('http') else ep_vid
        episodes.append({'number': ep_num, 'title': ep_title, 'url': ep_url, 'vid': ep_vid})
    if not episodes:
        # fallback: find all watch.php links and extract episode number from title
        for m in re.finditer(
            r'<a[^>]*title=(["\'])([^"\']+? الحلقة (\d+)[^"\']*)\1[^>]*href=(["\'])(watch\.php\?vid=[^"\']+)\4',
            html
        ):
            ep_title = m.group(2)
            ep_num = int(m.group(3))
            ep_vid = m.group(5)
            ep_url = BASE_URL + '/' + ep_vid if not ep_vid.startswith('http') else ep_vid
            episodes.append({'number': ep_num, 'title': ep_title, 'url': ep_url, 'vid': ep_vid})
    result['episodes'] = episodes
    return result


def scrape_series_details(driver, series_list, max_series=10, debug=False):
    results = []
    total = min(len(series_list), max_series)
    start_time = time.time()
    for idx, (s_name, s_info) in enumerate(list(series_list.items())[:max_series]):
        pbar = progress_bar(idx + 1, total, start_time)
        print(f'  [{idx+1}/{total}] {pbar} {s_name[:50]}...', end=' ')
        if not safe_driver_get(driver, s_info['sample_vid'], wait=5):
            results.append({
                'name': s_name, 'poster': s_info.get('thumb', ''),
                'description': '', 'series_url': '', 'episodes': []
            })
            print('TIMEOUT')
            continue
        html = driver.page_source
        if debug:
            safe = re.sub(r'[^\w]', '_', s_name)[:30]
            with open(f'debug_ahwaktv_ep_{safe}.html', 'w', encoding='utf-8') as f:
                f.write(html)
        info = parse_episode_page(html)
        if not info.get('series_name'):
            results.append({
                'name': s_name, 'poster': s_info.get('thumb', ''),
                'description': '', 'series_url': '', 'episodes': []
            })
            print('NO SERIES INFO')
            continue
        series_url = info.get('series_url', '')
        series_name = info.get('series_name', '')
        existing = [r for r in results if (series_url and r.get('series_url') == series_url) or (series_name and r.get('name') == series_name)]
        if existing:
            print(f'DUPLICATE ({existing[0]["name"]})')
            continue
        result = {
            'name': info.get('series_name', s_name),
            'poster': info.get('poster', s_info.get('thumb', '')),
            'description': info.get('description', ''),
            'series_url': series_url,
            'episodes': info.get('episodes', [])
        }
        results.append(result)
        print(f'{len(result["episodes"])} eps, poster={result["poster"][:50]}')
    return results


# ==================== PHASE 3: Extract embed URLs for ALL episodes ====================

def extract_servers(html):
    """Extract all video server URLs from WatchList on see.php page"""
    servers = []
    for m in re.finditer(
        r'<li[^>]*data-embed-url="([^"]*)"[^>]*>\s*<a[^>]*>\s*<strong>([^<]+)</strong>',
        html
    ):
        url = m.group(1)
        name = m.group(2).strip()
        if url and name:
            servers.append({'name': name, 'url': url})
    return servers


def sort_servers(servers):
    """Sort servers so 'Vidspeed' is first (default), rest maintain order"""
    vidspeed = [s for s in servers if 'vidspeed' in s['name'].lower()]
    others = [s for s in servers if 'vidspeed' not in s['name'].lower()]
    result = vidspeed + others
    for i, s in enumerate(result):
        s['isDefault'] = (i == 0)
    return result


def fetch_page_via_js(driver, url, timeout=10):
    script = f'''
        return new Promise((resolve) => {{
            const controller = new AbortController();
            const t = setTimeout(() => controller.abort(), {timeout * 1000});
            fetch('{url}', {{
                method: 'GET',
                signal: controller.signal
            }})
            .then(r => r.text())
            .then(resolve)
            .catch(e => resolve(''));
        }});
    '''
    try:
        return driver.execute_script(script)
    except:
        return ''


def fetch_many_via_js(driver, urls, timeout=10):
    """Fetch multiple URLs in parallel via JS fetch, returns dict of url->html"""
    script = f'''
        return new Promise((resolve) => {{
            const urls = {json.dumps(urls)};
            const controller = new AbortController();
            const t = setTimeout(() => controller.abort(), {timeout * 1000});
            Promise.all(urls.map(url =>
                fetch(url, {{method: 'GET', signal: controller.signal}})
                    .then(r => r.text())
                    .catch(e => '')
            )).then(results => {{
                const obj = {{}};
                urls.forEach((url, i) => {{ obj[url] = results[i]; }});
                resolve(obj);
            }});
        }});
    '''
    try:
        return driver.execute_script(script)
    except:
        return {}


def save_progress(series_data, output_path, script_dir):
    """Save both raw and formatted output files"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(series_data, f, ensure_ascii=False, indent=2)
    formatted = []
    for s in series_data:
        seasons = []
        if s['episodes']:
            seasons.append({
                'season': 1,
                'episodes': [{
                    'number': e['number'],
                    'title': e['title'],
                    'servers': e.get('servers', [{'name': 'watch', 'url': e['url'], 'isDefault': True}]),
                    'downloadServers': [{'name': 'رابط المشاهدة', 'url': e['url']}]
                } for e in s['episodes']]
            })
        formatted.append({
            'title': s['name'],
            'poster': s['poster'],
            'description': s['description'],
            'year': '',
            'type': 'تركي',
            'contentType': 'series',
            'seasons': seasons
        })
    fmt_path = os.path.join(script_dir, os.path.basename(output_path).replace('.json', '_formatted.json'))
    with open(fmt_path, 'w', encoding='utf-8') as f:
        json.dump(formatted, f, ensure_ascii=False, indent=2)
    return fmt_path


def scrape_embeds(driver, series_data, output_path, debug=False):
    BATCH_SIZE = 20
    total_series = len(series_data)
    phase3_start = time.time()
    for si, series in enumerate(series_data):
        eps = series['episodes']
        name = series['name'][:40]
        spbar = progress_bar(si + 1, total_series, phase3_start)
        print(f'  Series [{si+1}/{total_series}] {spbar} {name} ({len(eps)} eps)')
        
        url_to_ep = {}
        for ep in eps:
            if ep.get('servers'):
                continue
            vid_match = re.search(r'vid=([^&]+)', ep['url'])
            if vid_match:
                see_url = f'{BASE_URL}/see.php?vid={vid_match.group(1)}'
                url_to_ep[see_url] = ep
        
        if url_to_ep:
            all_urls = list(url_to_ep.keys())
            found = 0
            total_batches = max(1, (len(all_urls) - 1) // BATCH_SIZE + 1)
            batch_start = time.time()
            for i in range(0, len(all_urls), BATCH_SIZE):
                batch = all_urls[i:i+BATCH_SIZE]
                batch_idx = i // BATCH_SIZE + 1
                bpbar = progress_bar(batch_idx, total_batches, batch_start)
                print(f'    Batch {batch_idx}/{total_batches} {bpbar} ({len(batch)} eps)...', end=' ')
                results = fetch_many_via_js(driver, batch, timeout=15) or {}
                for see_url, html in results.items():
                    ep = url_to_ep[see_url]
                    if html:
                        servers = extract_servers(html)
                        if servers:
                            ep['servers'] = sort_servers(servers)
                            found += 1
                print(f'{sum(1 for u in batch if url_to_ep[u].get("servers"))}/{len(batch)}')
                if i + BATCH_SIZE < len(all_urls):
                    time.sleep(0.5)
            print(f'    => {found}/{len(url_to_ep)} OK')
        
        with_srv = sum(1 for e in eps if e.get('servers'))
        print(f'    => {with_srv}/{len(eps)} have servers')
        # Save after every series to avoid losing progress on crash
        save_progress(series_data, output_path, SCRIPT_DIR)


def make_options():
    o = uc.ChromeOptions()
    o.add_argument('--no-sandbox')
    o.add_argument('--window-size=1920,1080')
    return o

# ==================== MAIN ====================

def main():
    parser = argparse.ArgumentParser(description='AhwakTV Turkish Series Scraper')
    parser.add_argument('--start', type=int, default=1, help='First category page')
    parser.add_argument('--end', type=int, default=1, help='Last category page')
    parser.add_argument('--max-series', type=int, default=10, help='Max series to process')
    parser.add_argument('--episodes-only', action='store_true', help='Skip embed extraction')
    parser.add_argument('--output', default=os.path.join(SCRIPT_DIR, 'ahwaktv_data.json'), help='Output file')
    parser.add_argument('--debug', action='store_true', help='Save debug HTML')
    parser.add_argument('--rescue', action='store_true', help='Re-scrape series with 0 episodes from existing data')
    args = parser.parse_args()

    print('Launching browser...')
    driver = uc.Chrome(options=make_options(), version_main=148)

    try:
        print('Bypassing Cloudflare...')
        driver.get(BASE_URL)
        time.sleep(15)

        existing_data = load_existing_data(args.output)
        unique_series = {}
        all_eps = []

        print(f'\n{"="*60}')
        print(f'PHASE 1: Scraping category pages {args.start}-{args.end}')
        print(f'{"="*60}')
        all_eps, unique_series = scrape_category_pages(driver, args.start, args.end, args.debug)
        if not unique_series:
            print('ERROR: No series found.')
            sys.exit(1)
        print(f'Discovered {len(unique_series)} unique series')

        # === Filter: skip series that already exist in saved data with >= episodes ===
        existing_by_name = {s['name']: s for s in existing_data}
        existing_counts = {n: len(s['episodes']) for n, s in existing_by_name.items()}
        cat_counts = Counter()
        for ep in all_eps:
            cat_counts[extract_series_name(ep['title'])] += 1
        to_remove = []
        for name in list(unique_series.keys()):
            if name in existing_counts:
                cat_count = cat_counts.get(name, 0)
                # Never skip series with 0 existing episodes (so they get re-scraped with fixed regex)
                if existing_counts[name] > 0 and cat_count <= existing_counts[name]:
                    to_remove.append(name)
                    print(f'  SKIP "{name[:40]}": saved {existing_counts[name]} eps >= category {cat_count}')
        for name in to_remove:
            del unique_series[name]

        if args.rescue:
            # Rescue mode: keep only series that exist in saved data with 0 episodes
            zero_names = {s['name'] for s in existing_data if len(s.get('episodes', [])) == 0}
            to_remove = [name for name in list(unique_series.keys()) if name not in zero_names]
            for name in to_remove:
                del unique_series[name]
            args.max_series = max(args.max_series, len(unique_series))
            print(f'Rescue mode: {len(unique_series)} zero-episode series to re-scrape')
        else:
            print(f'After filtering: {len(unique_series)} series to scrape ({len(to_remove)} skipped)')

        # Restart browser to avoid session timeout / crash after Phase 1
        print('Restarting browser for Phase 2...')
        try: driver.quit()
        except: pass
        driver = uc.Chrome(options=make_options(), version_main=148)
        driver.get(BASE_URL)
        time.sleep(15)

        print(f'\n{"="*60}')
        print(f'PHASE 2: Scraping series details (max {args.max_series})')
        print(f'{"="*60}')
        if unique_series:
            new_data = scrape_series_details(driver, unique_series, args.max_series, args.debug)
        else:
            new_data = []
        if not new_data and not existing_data:
            print('ERROR: No series details extracted.')
            sys.exit(1)

        series_data = merge_series_data(existing_data, new_data)
        total_eps = sum(len(s['episodes']) for s in series_data)
        print(f'\nTotal: {len(series_data)} series, {total_eps} episodes (new: {len(new_data)})')

        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(series_data, f, ensure_ascii=False, indent=2)
        print(f'Saved intermediate: {args.output}')

        if args.episodes_only:
            print('Episodes-only mode.')
            driver.quit()
            sys.exit(0)

        # Restart browser again for Phase 3
        print('Restarting browser for Phase 3...')
        try: driver.quit()
        except: pass
        driver = uc.Chrome(options=make_options(), version_main=148)

        print(f'\n{"="*60}')
        print('PHASE 3: Extracting embed URLs for ALL episodes')
        print(f'{"="*60}')
        scrape_embeds(driver, series_data, args.output, args.debug)

        total_with_srv = sum(sum(1 for e in s['episodes'] if e.get('servers')) for s in series_data)
        print(f'\n{"="*60}')
        print(f'COMPLETE')
        print(f'Series: {len(series_data)}')
        print(f'Episodes: {total_eps}')
        print(f'With servers: {total_with_srv}')
        print(f'Output: {args.output}')
        print(f'Formatted: {os.path.join(SCRIPT_DIR, os.path.basename(args.output).replace(".json", "_formatted.json"))}')
        print(f'{"="*60}')

    finally:
        try: driver.quit()
        except: pass


if __name__ == '__main__':
    main()
