import requests
from bs4 import BeautifulSoup
import json
import re
import sys
import io
import os
import time
import glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
SCRIPT_DIR = os.path.dirname(__file__)
CACHE_FILE = os.path.join(SCRIPT_DIR, 'elcinema_cache.json')

def load_cache():
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def extract_work_details(work_url):
    try:
        r = requests.get(work_url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')

        poster = ''
        og_image = soup.find('meta', {'property': 'og:image'})
        if og_image and og_image.get('content'):
            poster = og_image['content']
        if not poster:
            tw_image = soup.find('meta', {'name': 'twitter:image'})
            if tw_image and tw_image.get('content'):
                poster = tw_image['content']
        if not poster:
            for img in soup.find_all('img'):
                src = img.get('src', '')
                if 'elcinema.com/uploads/' in src and any(x in src for x in ('_315x420', '_640x', '_320x')):
                    poster = src
                    break

        title_ar = ''
        for span in soup.find_all('span', class_='notranslate'):
            if span.get('dir') == 'rtl':
                title_ar = span.text.strip()
                break
        if not title_ar:
            h1 = soup.find('h1')
            if h1:
                title_ar = h1.text.strip()

        content_type = 'series' if 'مسلسل' in r.text[:3000] else 'movie'
        return {'title': title_ar, 'poster': poster, 'type': content_type, 'url': work_url}
    except:
        return None

def scrape_listing_page(page_url):
    cache = load_cache()
    try:
        r = requests.get(page_url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f'  Status {r.status_code}')
            return 0
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.find_all('a', href=True)
        work_urls = set()
        for a in links:
            href = a['href']
            m = re.search(r'/work/(\d+)/', href)
            if m and m.group(1) not in cache:
                work_urls.add(f'https://elcinema.com/work/{m.group(1)}/')
        print(f'  Found {len(work_urls)} new work URLs')
        for i, url in enumerate(work_urls):
            print(f'  [{i+1}/{len(work_urls)}] Scraping...', end=' ')
            result = extract_work_details(url)
            if result and result['title']:
                cache[result['title']] = result
                if result['poster']:
                    print(f'OK: {result["title"][:40]}')
                else:
                    print(f'No poster: {result["title"][:40]}')
            else:
                print('Failed')
            time.sleep(1)
        save_cache(cache)
        return len(work_urls)
    except Exception as e:
        print(f'  Error: {e}')
        return 0

def scrape_category(base_url, label, pages=5):
    total = 0
    for page in range(1, pages + 1):
        print(f'\n{label} - Page {page}:')
        url = f'{base_url}?page={page}' if page > 1 else base_url
        total += scrape_listing_page(url)
    print(f'\n{label} done. New entries: {total}')

def scrape_all():
    categories = [
        ('https://elcinema.com/ramadan/2025/?utf8=%E2%9C%93&order=&country=&genre=&page=', 'Ramadan 2025', 10),
        ('https://elcinema.com/ramadan/2026/?utf8=%E2%9C%93&order=&country=&genre=&page=', 'Ramadan 2026', 10),
    ]
    for base_url, label, pages in categories:
        for page in range(1, pages + 1):
            url = base_url + str(page)
            print(f'\n{label} - Page {page}:')
            scrape_listing_page(url)

def normalize(t):
    """Remove diacritics, extra spaces, common prefixes"""
    t = t.strip()
    t = re.sub(r'\s+', '', t)  # remove all spaces
    t = t.replace('2024', '').replace('2023', '').replace('2025', '').replace('2022', '').replace('2021', '').replace('2020', '')
    t = t.replace('2019', '').replace('2018', '').replace('2017', '').replace('2016', '').replace('2015', '')
    t = re.sub(r'^فيلم', '', t)
    t = re.sub(r'^مسلسل', '', t)
    t = re.sub(r'^فلم', '', t)
    t = t.strip()
    # Remove diacritics (Arabic tashkeel)
    t = re.sub(r'[\u064B-\u0652]', '', t)
    return t.lower()

def search_by_title(title, cache):
    best = None
    best_score = 0
    normalized = normalize(title)
    if not normalized:
        return None

    for cached_title, data in cache.items():
        cached_normalized = normalize(cached_title)

        # Exact match after normalization
        if normalized == cached_normalized:
            return data

        # One contains the other
        if normalized in cached_normalized or cached_normalized in normalized:
            score = max(len(normalized), len(cached_normalized)) / min(len(normalized), len(cached_normalized))
            if score > best_score:
                best_score = score
                best = data

        # Check if year+purpose differences are the only issue
        common_chars = sum(1 for c in normalized if c in cached_normalized)
        if common_chars > 0:
            similarity = common_chars / max(len(normalized), len(cached_normalized))
            if similarity > 0.8 and similarity > best_score:
                best_score = similarity
                best = data

    return best

def update_data_js(data_js_path, replace_all=False):
    cache = load_cache()
    if not cache:
        print('Cache is empty. Run --scrape first.')
        return

    print(f'Cache has {len(cache)} entries')
    print(f'Reading {data_js_path}...')

    with open(data_js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the array by tracking bracket depth
    arr_start = content.find('const contentData = [')
    if arr_start == -1:
        print('Could not find contentData in data.js')
        return
    arr_start = content.index('[', arr_start)

    depth = 0
    in_string = False
    escape = False
    arr_end = arr_start
    for i, ch in enumerate(content[arr_start:], start=arr_start):
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0:
                arr_end = i + 1
                break

    json_str = content[arr_start:arr_end]
    # Fix JSON issues (trailing commas, double commas)
    for _ in range(20):
        new_str = re.sub(r',\s*([}\]])', r'\1', json_str)  # trailing commas
        new_str = re.sub(r',\s*,', r',', new_str)  # double commas
        if new_str == json_str:
            break
        json_str = new_str
    data = json.loads(json_str)
    broken_domains = ['egydead.fyi', 'cimaa4u.com']
    replacements = 0
    skipped_no_cache = 0

    for i, item in enumerate(data):
        title = item.get('title', '')
        old_poster = item.get('poster', '')
        should_replace = replace_all or any(d in old_poster for d in broken_domains)
        if not should_replace:
            continue
        result = search_by_title(title, cache)
        if result and result.get('poster'):
            old_url = data[i]['poster']
            new_url = result['poster']
            if old_url != new_url:
                data[i]['poster'] = new_url
                replacements += 1
                print(f'  [{replacements}] {title[:50]}')
                print(f'    Old: {old_url[:60]}...')
                print(f'    New: {new_url[:60]}...')
            else:
                skipped_no_cache += 1
        else:
            print(f'  [SKIP] {title[:50]} (not in cache)')
            skipped_no_cache += 1

    if replacements > 0:
        new_content = content[:arr_start] + json.dumps(data, ensure_ascii=False) + content[arr_end:]
        with open(data_js_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'\nReplaced {replacements} poster URLs in data.js')
    else:
        print('\nNo replacements made')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage:')
        print('  Search:      python elcinema_search.py <movie name>')
        print('  Build cache:  python elcinema_search.py --scrape')
        print('  Update data:  python elcinema_search.py --update        (broken posters only)')
        print('  Update all:   python elcinema_search.py --update-all    (all matched entries)')
        sys.exit(1)

    if sys.argv[1] == '--scrape':
        scrape_all()
    elif sys.argv[1] == '--update':
        data_path = os.path.join(SCRIPT_DIR, 'data.js')
        if os.path.exists(data_path):
            update_data_js(data_path, replace_all=False)
        else:
            print(f'data.js not found at {data_path}')
    elif sys.argv[1] == '--update-all':
        data_path = os.path.join(SCRIPT_DIR, 'data.js')
        if os.path.exists(data_path):
            update_data_js(data_path, replace_all=True)
        else:
            print(f'data.js not found at {data_path}')
    else:
        cache = load_cache()
        print(f'Cache has {len(cache)} entries')
        name = ' '.join(sys.argv[1:])
        result = search_by_title(name, cache)
        if result:
            print(f'Title: {result["title"]}')
            print(f'Poster: {result["poster"]}')
            print(f'Type: {result["type"]}')
        else:
            print(f'Not found. Try: python elcinema_search.py --scrape')
