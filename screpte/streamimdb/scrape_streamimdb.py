import json, re, os, sys, time
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(OUTPUT_DIR, exist_ok=True)

STATE_PATH = os.path.join(OUTPUT_DIR, 'state.json')

BASE_URL = 'https://streamimdb.ru'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}
DELAY = 0.5
TOTAL_PAGES = 2602
PER_PAGE = 35


def parse_movie_card(card):
    a_tag = card.find('a')
    if not a_tag:
        return None
    href = a_tag.get('href', '')
    m = re.match(r'/movie/([^/]+)', href)
    if not m:
        return None
    slug = m.group(1)

    img = card.find('img')
    title = img.get('alt', '').strip() if img else ''
    poster = img.get('src', '') if img else ''

    badge = card.find('span', class_='cb-card-badge')
    content_type = badge.get_text(strip=True) if badge else 'Movie'

    meta = card.find('p', class_='cb-card-meta')
    year = meta.get_text(strip=True) if meta else ''

    h3 = card.find('h3', class_='cb-card-title')
    if h3:
        title = h3.get_text(strip=True)

    return {
        'slug': slug,
        'title': title,
        'year': year,
        'poster': poster,
        'contentType': content_type.lower(),
        'watch_server': 'streamimdb.ru',
        'watch_server_url': '',
    }


def scrape_page(page_num):
    url = f'{BASE_URL}/movies?vaplayer_path=movies&page={page_num}'
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.encoding = 'utf-8'
        if r.status_code != 200:
            print(f'    HTTP {r.status_code}')
            return None
    except Exception as e:
        print(f'    Request error: {e}')
        return None

    soup = BeautifulSoup(r.text, 'html.parser')
    cards = soup.find_all('div', class_='cb-card')
    results = []
    for card in cards:
        parsed = parse_movie_card(card)
        if parsed:
            results.append(parsed)
    return results


def fetch_embed_id(slug):
    """Visit movie detail page to extract numeric embed ID from data-src."""
    url = f'{BASE_URL}/movie/{slug}'
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return None
        m = re.search(r'data-src="(/embed/movie/\d+)"', r.text)
        if m:
            return m.group(1)
    except:
        pass
    return None


def load_existing(output_path):
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def get_processed_slugs(results):
    slugs = set()
    for r in results:
        if r.get('slug'):
            slugs.add(r['slug'])
    return slugs


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_state(data):
    """Merge new keys into existing state (don't overwrite unrelated keys)."""
    state = load_state()
    state.update(data)
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def phase_listings(all_movies, processed_slugs, pages_to_scrape, output_path, resume, page_from=0, page_to=0):
    print('=== Phase 1: Listing pages ===')

    if page_to == 0:
        page_to = pages_to_scrape

    if resume and page_from == 0:
        state = load_state()
        start_page = state.get('listings_page', 0) + 1
    else:
        start_page = page_from if page_from > 0 else 1

    if start_page > page_to:
        print(f'  Page range {start_page}-{page_to} already done.')
        return

    for page in range(start_page, page_to + 1):
        print(f'Page {page}/{page_to}... ', end='', flush=True)
        movies = scrape_page(page)
        if movies is None:
            print('FAILED')
            time.sleep(5)
            continue

        new_count = 0
        for m in movies:
            if m['slug'] not in processed_slugs:
                all_movies.append(m)
                processed_slugs.add(m['slug'])
                new_count += 1

        print(f'{len(movies)} movies ({new_count} new)')

        save_state({'listings_page': page})

        if page % 25 == 0:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_movies, f, ensure_ascii=False, indent=2)
            print(f'  [Checkpoint: {len(all_movies)} movies]')

        time.sleep(DELAY)


def batch_fetch_embeds(slug_list, n_workers=5):
    """Fetch embed IDs for multiple slugs concurrently."""
    results = {}
    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        fut_map = {pool.submit(fetch_embed_id, slug): slug for slug in slug_list}
        for fut in as_completed(fut_map):
            results[fut_map[fut]] = fut.result()
    return results


def phase_embeds(all_movies, output_path, resume, embed_from=0, embed_to=-1, parallel=5, embed_from_set=False):
    print('\n=== Phase 2: Fetching embed IDs ===')
    state = load_state()
    processed_idx = state.get('embeds_index', -1) if resume else -1

    end_idx = embed_to if embed_to >= 0 else len(all_movies)

    if resume and not embed_from_set:
        to_process = [(i, m) for i, m in enumerate(all_movies)
                      if embed_from <= i < end_idx
                      and i > processed_idx
                      and not m.get('watch_server_url')]
    else:
        to_process = [(i, m) for i, m in enumerate(all_movies)
                      if embed_from <= i < end_idx
                      and not m.get('watch_server_url')]

    if not to_process:
        print('  All embed IDs already fetched.')
        return

    n = len(to_process)
    print(f'  Processing {n} movies [{embed_from}-{end_idx}) with {parallel} workers')

    batch_size = parallel * 5

    for batch_start in range(0, n, batch_size):
        batch = to_process[batch_start:batch_start + batch_size]

        slugs = [m['slug'] for _, m in batch]
        paths = batch_fetch_embeds(slugs, parallel)

        for j, (idx, m) in enumerate(batch):
            embed_path = paths.get(m['slug'])
            if embed_path:
                m['watch_server_url'] = f'{BASE_URL}{embed_path}'

            title_clean = m['title'][:50].encode('ascii', 'replace').decode('ascii')
            status = 'OK' if embed_path else 'NO ID'
            print(f'  [{idx}/{len(all_movies)}] {title_clean:50s} ... {status}')

            save_state({'embeds_index': idx})

        # Checkpoint every batch (save progress)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_movies, f, ensure_ascii=False, indent=2)

        done = min(batch_start + batch_size, n)
        print(f'    [Checkpoint: {done}/{n} processed]')


def main():
    if '--help' in sys.argv or '-h' in sys.argv:
        print(f'Usage: python {os.path.basename(__file__)} [options]')
        print('  --resume             Resume from last saved state')
        print('  --listings-only      Only scrape listing pages')
        print('  --embeds-only        Only fetch embed IDs')
        print('  --page-from N        Start listing from page N')
        print('  --page-to N          End listing at page N')
        print('  --from N             Start embed processing at index N')
        print('  --to N               End embed processing at index N')
        print('  --limit N            Max listing pages to scrape')
        print('  --fresh              Clear state and start fresh')
        print('  --parallel N         Concurrent requests for embeds (default 5)')
        return

    limit = 0
    resume = False
    listings_only = False
    embeds_only = False
    embed_from = 0
    embed_to = -1
    embed_from_set = False
    page_from = 0
    page_to = 0
    fresh = False
    parallel = 5
    args = sys.argv[1:]
    while args:
        if args[0] == '--limit' and len(args) > 1:
            limit = int(args[1])
            args = args[2:]
        elif args[0] == '--resume':
            resume = True
            args = args[1:]
        elif args[0] == '--listings-only':
            listings_only = True
            args = args[1:]
        elif args[0] == '--embeds-only':
            embeds_only = True
            args = args[1:]
        elif args[0] == '--from' and len(args) > 1:
            embed_from = int(args[1])
            embed_from_set = True
            args = args[2:]
        elif args[0] == '--to' and len(args) > 1:
            embed_to = int(args[1])
            args = args[2:]
        elif args[0] == '--page-from' and len(args) > 1:
            page_from = int(args[1])
            args = args[2:]
        elif args[0] == '--page-to' and len(args) > 1:
            page_to = int(args[1])
            args = args[2:]
        elif args[0] == '--fresh':
            fresh = True
            args = args[1:]
        elif args[0] == '--parallel' and len(args) > 1:
            parallel = int(args[1])
            args = args[2:]
        else:
            args = args[1:]

    output_path = os.path.join(OUTPUT_DIR, 'streamimdb_movies.json')

    if fresh:
        save_state({})

    all_movies = load_existing(output_path) if (os.path.exists(output_path) and not fresh) else []
    processed_slugs = get_processed_slugs(all_movies)

    if resume and all_movies:
        print(f'Resuming: {len(all_movies)} movies already saved')
        valid = sum(1 for m in all_movies if m.get('watch_server_url'))
        print(f'  {valid}/{len(all_movies)} have working embed URLs')

    if limit > 0:
        pages_to_scrape = min(limit, TOTAL_PAGES)
    else:
        pages_to_scrape = TOTAL_PAGES

    if not embeds_only:
        phase_listings(all_movies, processed_slugs, pages_to_scrape, output_path, resume, page_from, page_to)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_movies, f, ensure_ascii=False, indent=2)

        if listings_only:
            print(f'\nListings only: {len(all_movies)} movies saved')
            return

    # Phase 2: embed IDs
    phase_embeds(all_movies, output_path, resume, embed_from, embed_to, parallel, embed_from_set)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_movies, f, ensure_ascii=False, indent=2)

    with_embeds = sum(1 for m in all_movies if m.get('watch_server_url'))
    print(f'\nSaved {len(all_movies)} movies to {output_path}')
    print(f'Movies with working embeds: {with_embeds}/{len(all_movies)}')


if __name__ == '__main__':
    main()
