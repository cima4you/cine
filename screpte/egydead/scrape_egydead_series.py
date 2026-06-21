import json, os, re, sys, time, threading, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import unquote
sys.stdout.reconfigure(encoding='utf-8')

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data_egydead_series.json')
OUTPUT = os.path.normpath(OUTPUT)

BASE = 'https://tv8.egydead.live'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
}

import requests, urllib3
urllib3.disable_warnings()

_thread_local = threading.local()

def get_session():
    if not hasattr(_thread_local, 'sess'):
        import undetected_chromedriver as uc
        cache_dir = os.path.expanduser('~/.undetected_chromedriver')
        if os.path.exists(cache_dir):
            shutil.rmtree(cache_dir)
        driver = uc.Chrome(headless=False, version_main=148)
        driver.get(BASE)
        for i in range(60):
            time.sleep(1)
            title = driver.title
            src = driver.page_source
            if 'Un instant' not in title and 'Just a moment' not in title and 'challenge' not in src.lower()[:2000]:
                print(f'  Cloudflare solved after {i+1}s')
                break
            if i % 5 == 0:
                print(f'  Cloudflare challenge... ({i+1}) title={title}')
        time.sleep(2)
        cookies = driver.get_cookies()
        ua = driver.execute_script('return navigator.userAgent')
        driver.quit()

        sess = requests.Session()
        sess.headers.update({'User-Agent': ua})
        for c in cookies:
            sess.cookies.set(c['name'], c['value'], domain=c.get('domain', ''))
        sess.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
        })
        _thread_local.sess = sess
    return _thread_local.sess

def fetch(url, retries=3, post_data=None):
    for attempt in range(retries):
        try:
            sess = get_session()
            if post_data:
                resp = sess.post(url, data=post_data, timeout=30)
            else:
                resp = sess.get(url, timeout=30)
            if resp.status_code == 200 and 'Just a moment' not in resp.text:
                return resp.text
            time.sleep(2)
        except:
            if attempt == retries - 1:
                return None
            time.sleep(2)
    return None

def extract_slug(url):
    path = unquote(url.rstrip('/'))
    m = re.search(r'/مسلسل-(.+?)-الحلقة-\d+', path)
    if m:
        return m.group(1)
    m = re.search(r'/series/(.+?)(?:/|$)', path)
    if m:
        return m.group(1)
    return None

def parse_listing(html):
    items = []
    for m in re.finditer(r'<li class="movieItem">(.*?)</li>', html, re.DOTALL):
        item_html = m.group(1)
        href_m = re.search(r'<a[^>]*href="([^"]+)"', item_html)
        title_m = re.search(r'<h1[^>]*class="[^"]*BottomTitle[^"]*"[^>]*>([^<]+)</h1>', item_html)
        img_m = re.search(r'<img[^>]*src="([^"]+)"', item_html)
        cat_m = re.search(r'<span[^>]*class="[^"]*cat_name[^"]*"[^>]*>([^<]+)</span>', item_html)
        if href_m and title_m:
            href = href_m.group(1) if href_m.group(1).startswith('http') else BASE + href_m.group(1)
            items.append({
                'url': href,
                'title': title_m.group(1).strip(),
                'image': img_m.group(1) if img_m else '',
                'category_name': cat_m.group(1).strip() if cat_m else '',
            })
    return items

def scrape_page(page_num):
    url = f'{BASE}/series-category/turkish-series/page/{page_num}/' if page_num > 1 else f'{BASE}/series-category/turkish-series/'
    html = fetch(url)
    if not html:
        return []
    return parse_listing(html)

def scrape_series_page(series_url):
    html = fetch(series_url)
    if not html:
        return None

    desc = ''
    dm = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html)
    if dm:
        desc = dm.group(1)
    if not desc:
        dm = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html)
        if dm:
            desc = dm.group(1)

    poster = ''
    pm = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
    if pm:
        poster = pm.group(1)

    year = ''
    ym = re.search(r'(\d{4})', html)
    if ym:
        year = ym.group(1)

    story = ''
    sm = re.search(r'<div class="singleStory">(.*?)</div>', html, re.DOTALL)
    if sm:
        story = re.sub(r'<[^>]+>', '', sm.group(1)).strip()
    if not story:
        sm = re.search(r'<div class="extra-content">\s*<span>القصه</span>\s*<p>([^<]+)</p>', html, re.DOTALL)
        if sm:
            story = sm.group(1).strip()

    details = {}
    detail_section = re.search(r'<div class="LeftBox">\s*<ul>(.*?)</ul>', html, re.DOTALL)
    if detail_section:
        for li_html in re.findall(r'<li>(.*?)</li>', detail_section.group(1), re.DOTALL):
            span_m = re.search(r'<span>([^<]+)</span>', li_html)
            if not span_m:
                continue
            key = span_m.group(1).strip()
            links = re.findall(r'<a[^>]*>([^<]+)</a>', li_html)
            vals = [a.strip() for a in links if a.strip()]
            val = '، '.join(vals) if vals else ''
            if key and val and key not in details:
                details[key] = val

    genres = []
    for k, v in details.items():
        if 'النوع' in k or 'التصنيف' in k:
            genres = [g.strip() for g in v.split('،') if g.strip()]

    episodes = []
    for em in re.finditer(r'<li[^>]*class="[^"]*episodeItem[^"]*"[^>]*>(.*?)</li>', html, re.DOTALL):
        ep_html = em.group(1)
        ep_href = re.search(r'<a[^>]*href="([^"]+)"', ep_html)
        ep_title = re.search(r'<h1[^>]*>([^<]+)</h1>', ep_html)
        ep_num = re.search(r'الحلقة\s*(\d+)', ep_html)
        if ep_href:
            ep_url = ep_href.group(1) if ep_href.group(1).startswith('http') else BASE + ep_href.group(1)
            episodes.append({
                'url': ep_url,
                'title': ep_title.group(1).strip() if ep_title else '',
                'episode_number': ep_num.group(1) if ep_num else '',
            })

    if not episodes:
        for em in re.finditer(r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*episode[^"]*"', html, re.DOTALL):
            ep_url = em.group(1) if em.group(1).startswith('http') else BASE + em.group(1)
            episodes.append({'url': ep_url, 'title': '', 'episode_number': ''})

    return {
        'description': story or desc,
        'year': year,
        'poster': poster,
        'genres': genres,
        'details': details,
        'episodes': episodes,
    }

def scrape_episode_servers(ep_url):
    html = fetch(ep_url)
    if not html:
        return []

    servers = []
    data_links = re.findall(r'data-link="([^"]+)"', html)

    if not data_links:
        html_post = fetch(ep_url, post_data={'View': '1'})
        if html_post:
            data_links = re.findall(r'data-link="([^"]+)"', html_post)
            if html_post:
                html = html_post

    if data_links:
        server_names = re.findall(r'<li[^>]*data-link="[^"]*"[^>]*>\s*([^<]+?)\s*</li>', html, re.DOTALL)
        for idx, link in enumerate(data_links):
            name = server_names[idx].strip() if idx < len(server_names) and server_names[idx].strip() else f'server{idx+1}'
            link = link.strip()
            if link.startswith('/'):
                link = BASE + link
            elif link.startswith('//'):
                link = 'https:' + link
            servers.append({'name': name, 'url': link, 'isDefault': idx == 0})
    else:
        iframes = re.findall(r'<iframe[^>]*src="([^"]+)"', html)
        for idx, src in enumerate(iframes[:5]):
            if src:
                if src.startswith('/'):
                    src = BASE + src
                elif src.startswith('//'):
                    src = 'https:' + src
                servers.append({'name': f'server{idx+1}', 'url': src, 'isDefault': idx == 0})

    return servers

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Scrape EgyDead Turkish series')
    parser.add_argument('--start', type=int, default=1, help='Start page')
    parser.add_argument('--end', type=int, default=5, help='End page (inclusive)')
    parser.add_argument('--threads', type=int, default=3, help='Threads for scraping')
    parser.add_argument('--output', default=OUTPUT, help=f'Output file (default: {OUTPUT})')
    parser.add_argument('--resume', action='store_true', help='Skip series already in output')
    args = parser.parse_args()

    existing_slugs = set()
    if args.resume and os.path.exists(args.output):
        with open(args.output, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        for it in existing:
            s = it.get('_slug', '')
            if s:
                existing_slugs.add(s)
        print(f'Loaded {len(existing)} series ({len(existing_slugs)} slugs skipped)')

    print('\n[1/4] Getting Cloudflare session...')
    get_session()

    total_pages = args.end - args.start + 1
    print(f'\n[2/4] Scraping {total_pages} pages ({args.start}-{args.end})...')
    all_eps = []
    failed = 0
    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = {ex.submit(scrape_page, p): p for p in range(args.start, args.end+1)}
        for i, f in enumerate(as_completed(futures), 1):
            res = f.result()
            if res:
                all_eps.extend(res)
            else:
                failed += 1
            if i % 10 == 0 or i == total_pages:
                print(f'  Pages: {i}/{total_pages} | Items so far: {len(all_eps)} | Failed: {failed}')

    series_map = {}
    for ep in all_eps:
        title = ep.get('title', '')
        slug = title.lower().replace(' ', '-').replace('/', '-')
        slug = re.sub(r'[^\w\-]', '', slug)
        if not slug:
            slug = unquote(ep['url']).split('/')[-2] if '/' in ep['url'] else 'unknown'
        if slug not in series_map:
            series_map[slug] = {'slug': slug, 'eps': [], 'first': ep}
        series_map[slug]['eps'].append(ep)

    slugs = sorted(series_map.keys())
    print(f'\nUnique series: {len(slugs)}')

    todo_slugs = [s for s in slugs if s not in existing_slugs]
    print(f'To scrape: {len(todo_slugs)}, skipped: {len(slugs) - len(todo_slugs)}')

    print(f'\n[3/4] Scraping series details + servers...')
    results = []
    done = 0
    lock = threading.Lock()

    def process_series(slug):
        nonlocal done
        group = series_map[slug]
        first_ep = group['first']

        meta = scrape_series_page(first_ep['url'])

        all_servers = []
        ep_urls = list(set(ep['url'] for ep in group['eps']))
        for ep_url in ep_urls:
            servers = scrape_episode_servers(ep_url)
            all_servers.extend(servers)

        seen = set()
        unique_servers = []
        for sv in all_servers:
            if sv['url'] not in seen:
                seen.add(sv['url'])
                unique_servers.append({
                    'name': f'server{len(unique_servers)+1}',
                    'url': sv['url'],
                    'isDefault': len(unique_servers) == 0
                })

        title = first_ep.get('title', '')
        m = re.search(r'مسلسل\s+(.+?)\s+الموسم', title)
        if m:
            title = 'مسلسل ' + m.group(1).strip()
        elif not title:
            title = slug.replace('-', ' ').title()

        item = {
            'title': title,
            'year': (meta.get('year', '') if meta else '') or '2025',
            'rating': 'N/A',
            'duration': '',
            'quality': 'WEB-DL',
            'type': 'تركي',
            'description': (meta.get('description', '') if meta else '') or '',
            'cast': [' '],
            'categories': (meta.get('genres', []) if meta else []) or ['دراما'],
            'poster': (meta.get('poster', '') if meta else '') or first_ep.get('image', ''),
            'servers': unique_servers if unique_servers else [{'name': 'server1', 'url': '', 'isDefault': True}],
            'downloadServers': [],
            'trial': 'N/A',
            'contentType': 'series',
            '_slug': slug,
            '_url': first_ep['url'],
            '_ep_count': len(ep_urls),
        }

        with lock:
            done += 1
            if done % 5 == 0 or done == len(todo_slugs):
                print(f'  Series: {done}/{len(todo_slugs)}')
        return item

    if todo_slugs:
        with ThreadPoolExecutor(max_workers=args.threads) as ex:
            results = list(ex.map(process_series, todo_slugs))

    print(f'\n[4/4] Saving...')
    results.sort(key=lambda x: x.get('title', ''))

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'Saved {len(results)} series to {args.output}')

    with_servers = sum(1 for r in results if r.get('servers') and any(s.get('url') for s in r['servers']))
    print(f'Series with servers: {with_servers}/{len(results)}')
    total_eps = sum(r.get('_ep_count', 1) for r in results)
    print(f'Total episodes grouped: {total_eps}')

if __name__ == '__main__':
    main()
