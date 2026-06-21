import json, os, re, sys, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import unquote
sys.stdout.reconfigure(encoding='utf-8')

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data_arabseed.json')
OUTPUT = os.path.normpath(OUTPUT)

BASE = 'https://m.asd.ink'
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
        sess = requests.Session()
        sess.headers.update(HEADERS)
        sess.verify = False
        _thread_local.sess = sess
    return _thread_local.sess

def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            sess = get_session()
            resp = sess.get(url, timeout=30)
            if resp.status_code == 200:
                return resp.text
            time.sleep(1)
        except:
            if attempt == retries - 1:
                return None
            time.sleep(1)
    return None

def extract_slug(url):
    path = unquote(url.rstrip('/'))
    # Pattern 1: مسلسل-{SLUG}-s{SEASON}-eps{EPISODE}
    m = re.search(r'/%d9%85%d8%b3%d9%84%d8%b3%d9%84-(.+?)-s\d+-eps\d+', url)
    if m:
        return m.group(1)
    m = re.search(r'/مسلسل-(.+?)-s\d+-eps\d+', path)
    if m:
        return m.group(1)
    # Pattern 2: مسلسل-{SLUG}-الحلقة-{EPISODE}
    m = re.search(r'/%d9%85%d8%b3%d9%84%d8%b3%d9%84-(.+?)-\xd8\xa7%d9%84%d8%ad%d9%84%d9%82%d8%a9-\d+', url)
    if m:
        return m.group(1)
    m = re.search(r'/مسلسل-(.+?)-الحلقة-\d+', path)
    if m:
        return m.group(1)
    return None

def parse_listing(html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    for li in soup.select('li.box__xs__2'):
        a = li.select_one('a.movie__block')
        if not a:
            continue
        href = a.get('href', '')
        is_episode = 'is__episode' in (a.get('class', []) or [])
        if not is_episode:
            continue
        slug = extract_slug(href)
        if not slug:
            continue
        title = a.get('title', '') or ''
        img = li.select_one('img.images__loader')
        poster = img.get('data-src', '') if img else ''
        rating = li.select_one('.post__ratings')
        rating = rating.get_text(strip=True) if rating else ''
        genre = li.select_one('.__genre')
        genre = genre.get_text(strip=True) if genre else ''
        ep_num = li.select_one('.__number span')
        ep_num = ep_num.get_text(strip=True) if ep_num else ''
        items.append({
            'slug': slug,
            'url': href,
            'title': title,
            'poster': poster,
            'rating': rating,
            'genre': genre,
            'episode_number': ep_num,
        })
    return items

def scrape_page(page_num):
    url = f'{BASE}/category/turkish-series-2/page/{page_num}/'
    html = fetch(url)
    if not html:
        return []
    items = parse_listing(html)
    return items

def scrape_episode_servers(ep_url):
    html = fetch(ep_url)
    if not html:
        return []
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    watch_btn = soup.select_one('a.btton.watch__btn')
    if not watch_btn:
        return []
    watch_url = watch_btn.get('href', '')
    if not watch_url:
        return []
    watch_url = watch_url if watch_url.startswith('http') else BASE + watch_url
    watch_html = fetch(watch_url)
    if not watch_html:
        return []
    ws = BeautifulSoup(watch_html, 'html.parser')
    servers = []
    for sv in ws.select('.servers__list li[data-link]'):
        link = sv.get('data-link', '').strip()
        if link:
            if link.startswith('/'):
                link = BASE + link
            elif link.startswith('//'):
                link = 'https:' + link
            servers.append(link)
    return servers

def scrape_series_metadata(first_ep_url):
    html = fetch(first_ep_url)
    if not html:
        return {}
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    desc = ''
    story = soup.select_one('div.post__story p')
    if story:
        desc = story.get_text(strip=True)
    if not desc:
        short = soup.select_one('p.post__content')
        if short:
            desc = short.get_text(strip=True)
    year = ''
    duration = ''
    details_ul = soup.select_one('ul.info__area__ul')
    if details_ul:
        for li in details_ul.select('li'):
            label_span = li.select_one('.title__kit span')
            if not label_span:
                continue
            label = label_span.get_text(strip=True)
            if 'سنة العرض' in label:
                a = li.select_one('.tags__list a')
                if a:
                    year = a.get_text(strip=True)
            elif 'مدة العرض' in label:
                a = li.select_one('a[href="javascript:;"]')
                if a:
                    duration = a.get_text(strip=True)
    poster_img = soup.select_one('.poster__single img.poster-img')
    poster = ''
    if poster_img:
        poster = poster_img.get('src', '') or poster_img.get('srcset', '').split(' ')[0]
    return {'description': desc, 'year': year, 'duration': duration, 'poster': poster}

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Scrape Arabseed Turkish series (grouped by series)')
    parser.add_argument('--start', type=int, default=1, help='Start page')
    parser.add_argument('--end', type=int, default=5, help='End page (inclusive)')
    parser.add_argument('--threads', type=int, default=5, help='Threads for scraping')
    parser.add_argument('--output', default=OUTPUT, help=f'Output file (default: {OUTPUT})')
    parser.add_argument('--resume', action='store_true', help='Skip series slugs already in output')
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

    # Step 1: Scrape all listing pages, collect episodes grouped by slug
    total_pages = args.end - args.start + 1
    print(f'Scraping {total_pages} pages ({args.start}-{args.end})...')
    all_eps = []
    failed = 0
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(scrape_page, p): p for p in range(args.start, args.end+1)}
        for i, f in enumerate(as_completed(futures), 1):
            res = f.result()
            if res:
                all_eps.extend(res)
            else:
                failed += 1
            if i % 20 == 0 or i == total_pages:
                print(f'  Pages: {i}/{total_pages} | Episodes so far: {len(all_eps)} | Failed: {failed}')

    # Step 2: Group by slug
    series_map = {}
    for ep in all_eps:
        slug = ep['slug']
        if slug not in series_map:
            series_map[slug] = {'slug': slug, 'eps': [], 'first': ep}
        series_map[slug]['eps'].append(ep)

    slugs = sorted(series_map.keys())
    print(f'Unique series: {len(slugs)}')

    # Filter out already-done slugs
    todo_slugs = [s for s in slugs if s not in existing_slugs]
    print(f'To scrape: {len(todo_slugs)}, skipped: {len(slugs) - len(todo_slugs)}')

    # Step 3: Scrape metadata + servers for each series
    results = []
    done = 0
    lock = threading.Lock()

    def process_series(slug):
        group = series_map[slug]
        first_ep = group['first']
        # Get metadata from first episode page
        meta = scrape_series_metadata(first_ep['url'])
        # Get all episode URLs
        ep_urls = list(set(ep['url'] for ep in group['eps']))
        # Scrape servers for each episode
        all_servers = []
        for ep_url in ep_urls:
            servers = scrape_episode_servers(ep_url)
            all_servers.extend(servers)
        # Deduplicate servers
        seen = set()
        unique_servers = []
        for sv in all_servers:
            if sv not in seen:
                seen.add(sv)
                unique_servers.append({'name': f'server{len(unique_servers)+1}', 'url': sv, 'isDefault': len(unique_servers) == 0})
        item = {
            'title': '',
            'year': meta.get('year', '2025'),
            'rating': first_ep.get('rating', 'N/A'),
            'duration': meta.get('duration', ''),
            'quality': 'WEB-DL',
            'type': 'تركي',
            'description': meta.get('description', ''),
            'cast': [' '],
            'categories': [first_ep.get('genre', 'دراما')] if first_ep.get('genre') else ['دراما'],
            'poster': meta.get('poster', first_ep.get('poster', '')),
            'servers': unique_servers if unique_servers else [{'name': 'server1', 'url': '', 'isDefault': True}],
            'downloadServers': [],
            'trial': 'N/A',
            'contentType': 'movie',
            '_slug': slug,
            '_url': first_ep['url'],
            '_ep_count': len(ep_urls),
        }
        with lock:
            nonlocal done
            done += 1
            if done % 5 == 0 or done == len(todo_slugs):
                print(f'  Series: {done}/{len(todo_slugs)}')
        return item

    if todo_slugs:
        with ThreadPoolExecutor(max_workers=args.threads) as ex:
            results = list(ex.map(process_series, todo_slugs))

    # Step 4: Generate clean titles
    for item in results:
        slug = item.get('_slug', '')
        # Try to make a readable title from slug
        title = slug.replace('-', ' ').replace('_', ' ').title()
        # If we have the first ep title, extract series name from it
        first_title = ''
        if slug in series_map:
            first_title = series_map[slug]['first'].get('title', '')
        if first_title:
            # Extract base series name from episode title
            m = re.search(r'^مسلسل\s+(.+?)\s+الموسم', first_title)
            if m:
                title = 'مسلسل ' + m.group(1).strip()
            else:
                title = first_title
        item['title'] = title

    # Sort by title
    results.sort(key=lambda x: x.get('title', ''))

    # Save
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f'\nSaved {len(results)} series to {args.output}')

    # Stats
    with_servers = sum(1 for r in results if r.get('servers') and any(s.get('url') for s in r['servers']))
    print(f'Series with servers: {with_servers}/{len(results)}')
    total_eps = sum(r.get('_ep_count', 1) for r in results)
    print(f'Total episodes grouped: {total_eps}')

if __name__ == '__main__':
    main()
