#!/usr/bin/env python3
"""
Comprehensive Yam.AhwakTV Scraper
==================================
Scrapes ALL categories from yam.ahwaktv.net — series and movies — with
full episode lists and video server/embed URLs.

Output: JSON files in data.js-compatible format.

Usage:
    python scrape_yam_all.py                    # scrape all categories
    python scrape_yam_all.py --cat arabic-series # single category
    python scrape_yam_all.py --max 50            # limit items per category
    python scrape_yam_all.py --episodes-only     # skip server extraction
    python scrape_yam_all.py --fresh            # start fresh (overwrite existing)
"""
import sys, time, json, os, re, argparse, urllib.request, urllib.parse
from collections import OrderedDict

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'https://yam.ahwaktv.net'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = SCRIPT_DIR
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

DELAY = 0.5  # seconds between requests

# =========================== CATEGORIES ===========================
CATEGORIES = OrderedDict([
    # Arabic series (Ramadan)
    ('arabic-series-2026', {'slug': 'ramdan-series-2026', 'type': 'series', 'content_type': 'عربي', 'year': '2026'}),
    ('arabic-series-2025', {'slug': 'moslslat-ramdan-2025', 'type': 'series', 'content_type': 'عربي', 'year': '2025'}),
    ('arabic-series-2024', {'slug': 'moslslat-ramadan-2024', 'type': 'series', 'content_type': 'عربي', 'year': '2024'}),
    ('arabic-series-2023', {'slug': 'moslslat-ramdan-2023', 'type': 'series', 'content_type': 'عربي', 'year': '2023'}),
    ('arabic-series-2022', {'slug': 'moslslat-ramdan-2022', 'type': 'series', 'content_type': 'عربي', 'year': '2022'}),
    ('arabic-series-2021', {'slug': 'moslslat-ramdan-2021', 'type': 'series', 'content_type': 'عربي', 'year': '2021'}),
    # Arabic series (general)
    ('arabic-series-gen', {'slug': '1moslslat-arbyaa', 'type': 'series', 'content_type': 'عربي', 'year': ''}),
    ('egyptian-series', {'slug': 'moslslat-msriya', 'type': 'series', 'content_type': 'عربي', 'year': ''}),
    ('arabic-series-2023b', {'slug': 'moslslat-arbyaa-2023', 'type': 'series', 'content_type': 'عربي', 'year': '2023'}),
    ('khaleeji-series', {'slug': 'moslslat-Khalegia-2021', 'type': 'series', 'content_type': 'عربي', 'year': '2021'}),
    # Turkish series (translated/subtitled)
    ('turkish-series', {'slug': 'moslslat-turkiaa-motrgma', 'type': 'series', 'content_type': 'تركي', 'year': ''}),
    # Programs
    ('ramadan-programs-2023', {'slug': 'bramg-ramdan-2023', 'type': 'series', 'content_type': 'عربي', 'year': '2023'}),
    ('ramadan-programs-2022', {'slug': 'bramg-ramadan-2022', 'type': 'series', 'content_type': 'عربي', 'year': '2022'}),
    ('ramadan-programs-2021', {'slug': 'bramg-ramdan-2021', 'type': 'series', 'content_type': 'عربي', 'year': '2021'}),
    # Arabic movies
    ('arabic-movies', {'slug': 'aflam-arabya1', 'type': 'movie', 'content_type': 'عربي', 'year': ''}),
    ('arabic-movies-2022', {'slug': 'aflam-arabia-2022', 'type': 'movie', 'content_type': 'عربي', 'year': '2022'}),
    ('arabic-movies-2021', {'slug': 'arabic-films-2021', 'type': 'movie', 'content_type': 'عربي', 'year': '2021'}),
    # English movies
    ('english-movies', {'slug': 'english-movies', 'type': 'movie', 'content_type': 'أجنبي', 'year': ''}),
    ('english-movies-2026', {'slug': 'English-movies-2026', 'type': 'movie', 'content_type': 'أجنبي', 'year': '2026'}),
    ('english-movies-2023', {'slug': 'english-movies-2023', 'type': 'movie', 'content_type': 'أجنبي', 'year': '2023'}),
    ('english-movies-2022', {'slug': 'english-movies-2022', 'type': 'movie', 'content_type': 'أجنبي', 'year': '2022'}),
    ('english-movies-2021', {'slug': 'aflam-online-2021', 'type': 'movie', 'content_type': 'أجنبي', 'year': '2021'}),
    # Other movies
    ('turkish-movies', {'slug': 'aflam-turky', 'type': 'movie', 'content_type': 'تركي', 'year': ''}),
    ('hindi-movies', {'slug': 'aflam-hindi', 'type': 'movie', 'content_type': 'هندي', 'year': ''}),
    ('cartoon-movies', {'slug': 'aflam-cartoon', 'type': 'movie', 'content_type': 'انمي', 'year': ''}),
    ('asian-movies', {'slug': 'Asian-Movies', 'type': 'movie', 'content_type': 'أسيوي', 'year': ''}),
    ('dubbed-movies', {'slug': 'aflam-dub', 'type': 'movie', 'content_type': 'أجنبي', 'year': ''}),
    # Asian series
    ('asian-series', {'slug': 'moslslat-asia', 'type': 'series', 'content_type': 'أسيوي', 'year': ''}),
])


def log(msg):
    print(msg, flush=True)


def fetch(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
            resp = urllib.request.urlopen(req, timeout=30)
            return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < max_retries - 1:
                log(f'  Retry {attempt+1}: {e}')
                time.sleep(2)
            else:
                log(f'  Failed: {e}')
                return None


def extract_items(html):
    """Extract all video items from a category page"""
    items = []
    for m in re.finditer(r'<li class="col-xs-6 col-sm-4 col-md-3">(.*?)</li>', html, re.DOTALL):
        item_html = m.group(1)
        title_m = re.search(r'alt="([^"]*)"', item_html)
        echo_m = re.search(r'data-echo\s*=\s*["\']([^"\']*)["\']', item_html)
        # Find watch.php link specifically (skip modal/login links)
        link_m = re.search(r'href="([^"]*watch\.php[^"]*)"', item_html)
        if not link_m:
            link_m = re.search(r'href="([^"]*vid=[^"]+)"', item_html)
        if title_m and echo_m:
            items.append({
                'title': title_m.group(1).strip(),
                'poster': echo_m.group(1).strip(),
                'link': link_m.group(1).strip() if link_m else '',
            })
    return items


def extract_max_page(html):
    """Find the last page number from pagination links"""
    pages = re.findall(r'page=(\d+)', html)
    if pages:
        return max(int(p) for p in pages if p.isdigit())
    return 1


def is_watch_link(url):
    return 'watch.php' in url


def extract_vid(url):
    m = re.search(r'vid=([^&]+)', url)
    return m.group(1) if m else ''


def fetch_see_page(vid):
    """Fetch see.php page which contains embed server list"""
    url = f'{BASE_URL}/see.php?vid={vid}'
    return fetch(url)


def extract_servers(html):
    """Extract embed server URLs from see.php page"""
    servers = []
    for m in re.finditer(r'<li[^>]*data-embed-url="([^"]*)"[^>]*>\s*<a[^>]*>\s*<strong>([^<]+)</strong>', html):
        url = m.group(1)
        name = m.group(2).strip()
        if url and name:
            servers.append({'name': name, 'url': url})
    if not servers:
        for m in re.finditer(r'data-embed-url="([^"]*)"[^>]*>\s*<a[^>]*>\s*<strong>([^<]+)</strong>', html):
            url = m.group(1)
            name = m.group(2).strip()
            if url and name:
                servers.append({'name': name, 'url': url})
    return servers


def sort_servers(servers):
    vidspeed = [s for s in servers if 'vidspeed' in s['name'].lower() or 'vidspeed' in s['url'].lower()]
    others = [s for s in servers if s not in vidspeed]
    result = vidspeed + others
    for i, s in enumerate(result):
        s['isDefault'] = (i == 0)
    return result


# ==================== WATCH PAGE PARSING ====================

def parse_watch_page_series(html, vid):
    """Parse a watch page for a series episode -> extract series info + all episodes"""
    result = {'series_name': '', 'poster': '', 'description': '', 'series_url': '', 'episodes': []}

    m = re.search(r'<h1 class="title">([^<]+)</h1>', html)
    if m:
        result['series_name'] = m.group(1).strip()

    m = re.search(r'view-serie\.php\?name=([^"\'&]+)', html)
    if m:
        name = urllib.parse.unquote(m.group(1).replace('-', ' ').replace('+', ' '))
        if not result['series_name']:
            result['series_name'] = name
        result['series_url'] = f'{BASE_URL}/view-serie.php?name={m.group(1)}'

    m = re.search(r'<div class="pm-series-brief">.*?<img[^>]*src="([^"]*)"', html, re.DOTALL)
    if m:
        result['poster'] = m.group(1)

    m = re.search(r'<div class="description">\s*<p>([^<]*)</p>', html, re.DOTALL)
    if m:
        desc = m.group(1).strip()
        # Clean repetitive prefix
        desc = re.sub(r'^مشاهدة وتحميل (مسلسل ){1,2}', '', desc)
        desc = re.sub(r'\s+ماي سيما.*$', '', desc)
        desc = re.sub(r'\s+على موقع اهواك TV\s*\.?\s*$', '', desc)
        result['description'] = desc.strip()

    eps = []
    for m in re.finditer(
        r'<a[^>]*title=(["\'])([^"\']+)\1[^>]*href=(["\'])(watch\.php\?vid=[^"\']+)\3[^>]*><em>(\d+)</em>',
        html
    ):
        ep_num = int(m.group(5))
        ep_title = m.group(2)
        ep_vid_url = m.group(4)
        full_url = f'{BASE_URL}/{ep_vid_url}' if not ep_vid_url.startswith('http') else ep_vid_url
        eps.append({'number': ep_num, 'title': ep_title, 'url': full_url})
    if not eps:
        for m in re.finditer(
            r'<a[^>]*title=(["\'])([^"\']+? الحلقة (\d+)[^"\']*)\1[^>]*href=(["\'])(watch\.php\?vid=[^"\']+)\4',
            html
        ):
            ep_num = int(m.group(3))
            ep_title = m.group(2)
            ep_vid_url = m.group(5)
            full_url = f'{BASE_URL}/{ep_vid_url}' if not ep_vid_url.startswith('http') else ep_vid_url
            eps.append({'number': ep_num, 'title': ep_title, 'url': full_url})

    # Remove duplicates by vid
    seen_vids = set()
    unique_eps = []
    for ep in eps:
        vid_key = extract_vid(ep['url'])
        if vid_key and vid_key not in seen_vids:
            seen_vids.add(vid_key)
            unique_eps.append(ep)
    result['episodes'] = unique_eps
    return result


def parse_watch_page_movie(html):
    """Parse a watch page for a movie -> extract poster, servers"""
    result = {'poster': '', 'description': '', 'servers': [], 'downloadServers': []}

    m = re.search(r'<div class="pm-video-head">.*?<img[^>]*src="([^"]*)"', html, re.DOTALL)
    if m:
        result['poster'] = m.group(1)
    if not result['poster']:
        m = re.search(r'property="og:image"[^>]*content="([^"]*)"', html)
        if m:
            result['poster'] = m.group(1)

    m = re.search(r'<div class="description">\s*<p>([^<]*)</p>', html, re.DOTALL)
    if m:
        result['description'] = m.group(1).strip()

    return result


# ==================== SERIES NAME CLEANING ====================

def clean_series_name(title):
    t = title.strip()
    t = re.sub(r'^مسلسل\s*', '', t)
    t = re.sub(r'\s*الحلقة\s*\d+.*$', '', t)
    t = re.sub(r'\s*(مترجمة|مدبلجة|مترجم|مدبلج)\s*$', '', t)
    t = re.sub(r'\s*(HD|720P|1080P|كامله|كاملة|والاخيرة)\s*$', '', t, flags=re.IGNORECASE)
    return t.strip()


def normalize(t):
    t = re.sub(r'[\u064B-\u0652]', '', t)  # remove diacritics
    t = re.sub(r'\s+', '', t)
    return t.strip().lower()


# ==================== SCRAPE CATEGORY ====================

def scrape_category(slug, cat_type, content_type_val, year, max_items=0,
                     start_page=1, end_page=0, episodes_only=False):
    """Scrape category pages and return items"""
    log(f'\n{"="*60}')
    log(f'Category: {slug} (type={cat_type}, content_type={content_type_val})')
    log(f'Pages: {start_page}-{end_page if end_page else "end"}')
    log(f'{"="*60}')

    all_items = []
    page = start_page
    empty_pages = 0

    while True:
        if end_page and page > end_page:
            break
        url = f'{BASE_URL}/category.php?cat={slug}&page={page}&order=DESC'
        log(f'  Page {page}...')
        html = fetch(url)
        if not html:
            empty_pages += 1
            if empty_pages >= 2:
                break
            page += 1
            continue
        empty_pages = 0

        items = extract_items(html)
        if not items:
            log(f'    No items - end of category')
            break

        log(f'    Found {len(items)} items')
        all_items.extend(items)

        if max_items and len(all_items) >= max_items:
            all_items = all_items[:max_items]
            break

        max_page = extract_max_page(html)
        if page >= max_page:
            break
        page += 1
        time.sleep(DELAY)

    log(f'  Total: {len(all_items)} items')
    return all_items


def normalize_series_name_for_dedup(name):
    return normalize(clean_series_name(name))


# ==================== MAIN ====================

def main():
    parser = argparse.ArgumentParser(description='Comprehensive Yam.AhwakTV Scraper')
    parser.add_argument('--cat', help='Single category ID to scrape')
    parser.add_argument('--max', type=int, default=0, help='Max items per category (0=unlimited)')
    parser.add_argument('--episodes-only', action='store_true', help='Skip server extraction')
    parser.add_argument('--series-only', action='store_true', help='Only scrape series categories')
    parser.add_argument('--movies-only', action='store_true', help='Only scrape movie categories')
    parser.add_argument('--output', default=os.path.join(OUTPUT_DIR, 'yam_all_data.json'), help='Output file')
    parser.add_argument('--fresh', action='store_true', help='Start fresh (overwrite existing output)')
    parser.add_argument('--start-page', type=int, default=1, help='First category page (default: 1)')
    parser.add_argument('--end-page', type=int, default=0, help='Last category page (0=auto)')
    parser.add_argument('--start-series', type=int, default=1, help='First series index to process (default: 1)')
    parser.add_argument('--end-series', type=int, default=0, help='Last series index to process (0=all)')
    args = parser.parse_args()

    output_path = args.output

    # Determine which categories to scrape
    categories_to_scrape = list(CATEGORIES.items())
    if args.cat:
        categories_to_scrape = [(k, v) for k, v in categories_to_scrape if k == args.cat]
    if args.series_only:
        categories_to_scrape = [(k, v) for k, v in categories_to_scrape if v['type'] == 'series']
    if args.movies_only:
        categories_to_scrape = [(k, v) for k, v in categories_to_scrape if v['type'] == 'movie']

    if not categories_to_scrape:
        log('No categories to scrape. Check --cat parameter.')
        sys.exit(1)

    all_series = {}
    all_movies = {}
    total_scraped = 0

    for cat_id, cat_info in categories_to_scrape:
        items = scrape_category(
            cat_info['slug'], cat_info['type'], cat_info['content_type'],
            cat_info['year'], args.max,
            start_page=args.start_page, end_page=args.end_page,
            episodes_only=args.episodes_only
        )

        if cat_info['type'] == 'series':
            # Group by series name, keep item with max episode count
            for item in items:
                series_name = clean_series_name(item['title'])
                norm = normalize(series_name)
                ep_match = re.search(r'الحلقة\s*(\d+)', item['title'])
                ep_num = int(ep_match.group(1)) if ep_match else 0
                if norm not in all_series:
                    all_series[norm] = {
                        'name': series_name,
                        'poster': item['poster'],
                        'year': cat_info['year'],
                        'type_label': cat_info['content_type'],
                        'sample_link': item['link'],
                        'norm': norm,
                        'max_ep': ep_num,
                    }
                elif ep_num > all_series[norm]['max_ep']:
                    # Replace with item that has more episodes
                    all_series[norm]['name'] = series_name
                    all_series[norm]['poster'] = item['poster']
                    all_series[norm]['sample_link'] = item['link']
                    all_series[norm]['max_ep'] = ep_num

            # ── Series processing (watch page → episodes → servers → save) ──
            unique_series = list(all_series.values())
            si = max(0, args.start_series - 1)
            ei = args.end_series if args.end_series else len(unique_series)
            unique_series = unique_series[si:ei]
            log(f'  Processing series {args.start_series}-{min(ei, len(all_series))} of {len(all_series)}')

            # Load existing output (default: append, --fresh to overwrite)
            if not args.fresh and os.path.exists(output_path):
                try:
                    with open(output_path, 'r', encoding='utf-8') as f:
                        output = json.load(f)
                    log(f'Loaded {len(output)} existing items – will skip duplicates')
                except Exception:
                    output = []
            else:
                output = []
            existing_keys = {normalize(item.get('title', '')) for item in output}

            def save_output(out):
                tmp = output_path + '.tmp'
                with open(tmp, 'w', encoding='utf-8') as f:
                    json.dump(out, f, ensure_ascii=False, indent=2)
                os.replace(tmp, output_path)

            for idx, series in enumerate(unique_series):
                norm = series['norm']
                if norm in existing_keys and not args.fresh:
                    log(f'  [{idx+1}/{len(unique_series)}] SKIP (already saved) – {series["name"][:50]}')
                    continue

                link = series['sample_link']
                if not link or not is_watch_link(link):
                    continue

                log(f'  [{idx+1}/{len(unique_series)}] {series["name"][:50]}...')
                sys.stdout.flush()
                html = fetch(link)
                if not html:
                    log('  FAILED')
                    continue

                info = parse_watch_page_series(html, extract_vid(link))
                ep_list = info.get('episodes', [])
                total_scraped += 1
                log(f'{len(ep_list)} eps')

                # Build output immediately with servers
                seasons = []
                if ep_list:
                    seasons.append({'season': 1, 'episodes': []})
                    for ep in sorted(ep_list, key=lambda x: x['number']):
                        ep_vid = extract_vid(ep['url'])
                        ep_servers = []
                        ep_download = [{'name': 'رابط المشاهدة', 'url': ep['url']}]
                        if not args.episodes_only and ep_vid:
                            see_html = fetch_see_page(ep_vid)
                            if see_html:
                                ep_servers = sort_servers(extract_servers(see_html))
                            time.sleep(DELAY)

                        seasons[0]['episodes'].append({
                            'episodeNumber': ep['number'],
                            'number': ep['number'],
                            'title': ep['title'],
                            'servers': ep_servers,
                            'downloadServers': ep_download,
                        })

                # Detect if series is complete (has "الاخيرة" in any episode title)
                has_final = any('الاخيرة' in e.get('title','') or 'الأخيرة' in e.get('title','') for e in ep_list)
                has_final_title = any(w in (info.get('series_name') or series['name']) for w in ['الاخيرة','والاخيرة','الأخيرة','والأخيرة','كاملة','كامله'])

                output.append({
                    'title': info.get('series_name') or series['name'],
                    'poster': info.get('poster', series.get('poster', '')),
                    'description': info.get('description', ''),
                    'year': series['year'],
                    'type': series['type_label'],
                    'contentType': 'series',
                    'isComplete': has_final or has_final_title,
                    'seasons': seasons,
                })
                save_output(output)
                log(f'  ► Saved {len(output)} items')
                time.sleep(DELAY)

        else:  # movie
            for item in items:
                norm = normalize(item['title'])
                if norm not in all_movies:
                    m = {
                        'title': item['title'],
                        'poster': item['poster'],
                        'year': cat_info['year'],
                        'type_label': cat_info['content_type'],
                        'link': item['link'],
                        'servers': [],
                        'downloadServers': [],
                    }
                    all_movies[norm] = m

    # ── Movie processing ──
    if all_movies:
        log(f'\n{"="*60}')
        log(f'Processing {len(all_movies)} unique movies')
        log(f'{"="*60}')
        if not os.path.exists(output_path):
            output = []
            existing_keys = set()
        else:
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    output = json.load(f)
                existing_keys = {normalize(item.get('title', '')) for item in output}
            except Exception:
                output = []
                existing_keys = set()

        def save_output(out):
            tmp = output_path + '.tmp'
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            os.replace(tmp, output_path)

        for m_idx, (norm, m) in enumerate(all_movies.items()):
            if norm in existing_keys and not args.fresh:
                log(f'  [{m_idx+1}/{len(all_movies)}] SKIP (already saved) – {m["title"][:50]}')
                continue

            log(f'  [{m_idx+1}/{len(all_movies)}] {m["title"][:50]}...')
            servers = []
            download = []
            if m.get('link') and is_watch_link(m['link']):
                if not args.episodes_only:
                    vid = extract_vid(m['link'])
                    if vid:
                        see_html = fetch_see_page(vid)
                        if see_html:
                            servers = sort_servers(extract_servers(see_html))
                        time.sleep(DELAY)
                download = [{'name': 'رابط المشاهدة', 'url': m['link']}]

            output.append({
                'title': m['title'],
                'poster': m.get('poster', ''),
                'year': m['year'],
                'type': m['type_label'],
                'contentType': 'movie',
                'servers': servers,
                'downloadServers': download,
            })
            save_output(output)
            log(f'  ► Saved {len(output)} items')

    # ── Final formatted copy ──
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            output = json.load(f)
        formatted_path = output_path.replace('.json', '_formatted.json')
        with open(formatted_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        log(f'\nFinal: {len(output)} items → {output_path}')
        log(f'Formatted: {formatted_path}')


if __name__ == '__main__':
    main()
