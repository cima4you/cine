import json, re, os, sys, time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
NO_URL_PATH = os.path.join(DATA_DIR, 'streamimdb_no_url.json')
FOUND_PATH = os.path.join(DATA_DIR, 'streamimdb_found.json')
MAIN_PATH = os.path.join(DATA_DIR, 'streamimdb_movies.json')

BASE_URL = 'https://streamimdb.ru'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def fetch_embed_id(slug):
    url = f'{BASE_URL}/movie/{slug}'
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            return None
        m = re.search(r'data-src="(/embed/movie/\d+)"', r.text)
        return m.group(1) if m else None
    except:
        return None


def batch_fetch(slugs, n_workers):
    results = {}
    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        fut_map = {pool.submit(fetch_embed_id, slug): slug for slug in slugs}
        for fut in as_completed(fut_map):
            slug = fut_map[fut]
            try:
                results[slug] = fut.result()
            except:
                results[slug] = None
    return results


def main():
    if '--help' in sys.argv or '-h' in sys.argv:
        print('Usage: python retry_embeds.py [options]')
        print('  --from N       Start index (default 0)')
        print('  --to N         End index (default all)')
        print('  --parallel N   Concurrent requests (default 10)')
        return

    embed_from = 0
    embed_to = -1
    parallel = 10

    args = sys.argv[1:]
    while args:
        if args[0] == '--from' and len(args) > 1:
            embed_from = int(args[1])
            args = args[2:]
        elif args[0] == '--to' and len(args) > 1:
            embed_to = int(args[1])
            args = args[2:]
        elif args[0] == '--parallel' and len(args) > 1:
            parallel = int(args[1])
            args = args[2:]
        else:
            args = args[1:]

    with open(NO_URL_PATH, 'r', encoding='utf-8') as f:
        no_url = json.load(f)

    end_idx = embed_to if embed_to >= 0 else len(no_url)
    to_process = no_url[embed_from:end_idx]
    n = len(to_process)

    if not to_process:
        print(f'No movies in range [{embed_from}-{end_idx})')
        return

    print('=' * 60)
    print(f'  Total movies without URL in file: {len(no_url)}')
    print(f'  Processing range: [{embed_from} - {end_idx-1}]')
    print(f'  Movies in this batch: {n}')
    print(f'  Parallel workers: {parallel}')
    print('=' * 60)

    batch_size = parallel * 5
    found_count = 0
    found_movies = []

    for batch_start in range(0, n, batch_size):
        batch = to_process[batch_start:batch_start + batch_size]
        slugs = [m['slug'] for m in batch]
        paths = batch_fetch(slugs, parallel)
        batch_found = 0

        for m in batch:
            embed_path = paths.get(m['slug'])
            if embed_path:
                m['watch_server_url'] = f'{BASE_URL}{embed_path}'
                m['_found_in_retry'] = True
                found_count += 1
                batch_found += 1
                found_movies.append(m)

        done = min(batch_start + batch_size, n)
        global_idx_start = batch_start + embed_from
        global_idx_end = done + embed_from - 1
        pct = found_count / (batch_start + len(batch)) * 100 if (batch_start + len(batch)) > 0 else 0
        print(f'  [{global_idx_start:5d}-{global_idx_end:5d}] '
              f'found {batch_found:3d}/{len(batch):3d}  '
              f'| total so far: {found_count:4d}/{batch_start+len(batch):4d} ({pct:.1f}%)')

    print()
    print('=' * 60)
    print(f'  RESULTS')
    print(f'  Batch range: [{embed_from} - {end_idx-1}]')
    print(f'  Total processed: {n}')
    print(f'  Found URLs: {found_count}')
    print(f'  Still without URL: {n - found_count}')
    print('=' * 60)

    # Save found movies to separate file
    if found_movies:
        # Remove _found_in_retry flag before saving
        for m in found_movies:
            m.pop('_found_in_retry', None)
        with open(FOUND_PATH, 'w', encoding='utf-8') as f:
            json.dump(found_movies, f, ensure_ascii=False, indent=2)
        print(f'\nSaved {len(found_movies)} found movies to streamimdb_found.json')

    # Merge found movies into main file
    if found_movies and os.path.exists(MAIN_PATH):
        with open(MAIN_PATH, 'r', encoding='utf-8') as f:
            main_data = json.load(f)
        main_slugs = {m['slug'] for m in main_data}
        added = 0
        for m in found_movies:
            if m['slug'] not in main_slugs:
                main_data.append(m)
                added += 1
            else:
                for existing in main_data:
                    if existing['slug'] == m['slug']:
                        existing['watch_server_url'] = m['watch_server_url']
                        break
        with open(MAIN_PATH, 'w', encoding='utf-8') as f:
            json.dump(main_data, f, ensure_ascii=False, indent=2)
        print(f'Merged into streamimdb_movies.json: {len(main_data)} total')

    # Save remaining movies (still without URL) back to no_url file
    remaining = [m for m in no_url if not m.get('watch_server_url')]
    with open(NO_URL_PATH, 'w', encoding='utf-8') as f:
        json.dump(remaining, f, ensure_ascii=False, indent=2)
    print(f'Remaining movies without URL saved to streamimdb_no_url.json: {len(remaining)}')


if __name__ == '__main__':
    main()
