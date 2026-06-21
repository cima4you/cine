import requests, re, json, concurrent.futures, base64, time
from difflib import SequenceMatcher

headers = {'User-Agent': 'Mozilla/5.0'}
FILM_PATTERN = r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+'

CATEGORIES = {
    'Arabic': 'https://tuktukhd.com/category/movies-2/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%b9%d8%b1%d8%a8%d9%8a',
    'Turkish': 'https://tuktukhd.com/category/movies-2/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%aa%d8%b1%d9%83%d9%8a',
    'Anime': 'https://tuktukhd.com/category/movies-2/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d9%86%d9%85%d9%8a',
    'Netflix': 'https://tuktukhd.com/category/movies-2/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d9%86%d8%aa%d9%81%d9%84%d9%8a%d9%83%d8%b3',
    'Documentary': 'https://tuktukhd.com/category/movies-2/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d9%88%d8%ab%d8%a7%d8%a6%d9%82%d9%8a',
}

def scrape_listing(url):
    try:
        r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        if r.status_code != 200: return []
        alts = re.findall(r'alt="([^"]+)"', r.text)
        hrefs = re.findall(FILM_PATTERN, r.text, re.IGNORECASE)
        results = []
        for alt, href in zip(alts, hrefs):
            alt = alt.strip()
            m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم', alt)
            if m:
                results.append({'name': m.group(1).strip(), 'year': m.group(2), 'url': href})
        return results
    except:
        return []

all_listed = []
for cat_name, cat_url in CATEGORIES.items():
    print('Scraping {} category...'.format(cat_name))
    count = 0
    for page in range(1, 51):
        url = '{}page/{}/'.format(cat_url, page) if page > 1 else cat_url
        entries = scrape_listing(url)
        if not entries and page > 1:
            break
        all_listed.extend(entries)
        count += len(entries)
        if page % 10 == 0 or page == 1:
            print('  Page {}: {} (total category: {})'.format(page, len(entries), count))
    print('  {} total: {} movies'.format(cat_name, count))

print('\nTotal from all categories: {}'.format(len(all_listed)))

# Deduplicate by URL
seen_urls = set()
deduped = []
for m in all_listed:
    if m['url'] not in seen_urls:
        seen_urls.add(m['url'])
        deduped.append(m)

print('After dedup: {} movies'.format(len(deduped)))

# Save index
with open('scripts/tuktukhd/data/tuktuk_other_categories.json', 'w', encoding='utf-8') as f:
    json.dump(deduped, f, ensure_ascii=False)
print('Saved scripts/tuktuk_other_categories.json')

# --- Matching phase ---
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

target_servers = ['متعدد الجودة', 'سيرفر متعدد الجودات', 'سرفر متعدد الجودات',
                  'سيرفر متعدد', 'سرفر متعدد', 'سيرفر رئيسي']

remaining = []
for idx, item in enumerate(data_js):
    if any(s.get('name', '') in target_servers for s in item.get('servers', [])):
        remaining.append({
            'idx': idx, 'title': item.get('title', '').strip(),
            'year': str(item.get('year', '')), 'type': item.get('type', '')
        })

print('\nItems needing update: {}'.format(len(remaining)))

def super_norm(t):
    t = t.lower().strip()
    t = re.sub(r'\s+\d{4}$', '', t)
    t = re.sub(r"[`'’‘:.,!?&/\-]", ' ', t)
    t = re.sub(r'\s+', '', t)
    return t.strip()

def title_similarity(a, b):
    a = super_norm(a)
    b = super_norm(b)
    if not a or not b:
        return 0
    if a == b:
        return 1.0
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    if len(short) >= 5 and short in long_:
        return 0.85 + len(short) / max(len(a), len(b)) * 0.15
    return SequenceMatcher(None, a, b).ratio()

matched = []
unmatched = []

for item in remaining:
    r_title = item['title']
    r_year = item['year']
    best = None
    best_score = 0
    
    for s in deduped:
        s_title = s['name']
        s_year = s['year']
        
        year_diff = abs(int(r_year) - int(s_year)) if r_year.isdigit() and s_year.isdigit() else 999
        if year_diff > 1:
            continue
        
        score = title_similarity(r_title, s_title)
        min_score = 0.75 if year_diff == 0 else 0.85
        
        if score > best_score and score > min_score:
            best_score = score
            best = s
    
    if best and best_score > 0.75:
        matched.append({
            'idx': item['idx'], 'title': r_title, 'year': r_year,
            'type': item['type'], 'url': best['url'],
            'match_title': best['name'], 'match_year': best['year'],
            'score': round(best_score, 2)
        })
    else:
        unmatched.append(item)

print('Matched: {}'.format(len(matched)))
print('Unmatched: {}'.format(len(unmatched)))

if matched:
    print('\nMatched items:')
    for m in sorted(matched, key=lambda x: -x['score']):
        print('  "{}" ({}) -> "{}" ({}) [{:.2f}] {}'.format(
            m['title'], m['year'], m['match_title'], m['match_year'], m['score'], m['type']))

if unmatched:
    print('\nStill unmatched:')
    for m in unmatched:
        print('  "{}" ({}) [{}]'.format(m['title'], m['year'], m['type']))

if matched:
    print('\nVisiting {} pages...'.format(len(matched)))
    
    def extract(item):
        try:
            r = requests.get(item['url'], timeout=20, headers=headers)
            crypts = re.findall(r'data-crypt="([^"]+)"', r.text)
            watch_urls = [base64.b64decode(c).decode('utf-8') for c in crypts]
            dl_links = re.findall(r'data-real-url="([^"]+)"', r.text)
            si = re.findall(r'<li[^>]*class="[^"]*server--item[^"]*"[^>]*>.*?<span>([^<]*)</span>', r.text, re.DOTALL)
            sname = si[0].strip() if si else 'TukTuk Vip'
            return {
                'idx': item['idx'], 'title': item['title'],
                'watch_url': watch_urls[0] if watch_urls else None,
                'server_name': sname,
                'download_urls': dl_links,
                'success': len(watch_urls) > 0
            }
        except Exception as e:
            return {'idx': item['idx'], 'success': False, 'error': str(e)}
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(extract, m) for m in matched]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    successful = [r for r in results if r.get('success')]
    print('Success: {}, Failed: {}'.format(len(successful), len(results) - len(successful)))
    
    updated = 0
    for r in successful:
        idx = r['idx']
        item = data_js[idx]
        new_server = {'name': r['server_name'], 'url': r['watch_url'], 'isDefault': True}
        new_downloads = [{'name': 'TukTuk Download', 'url': dl} for dl in r.get('download_urls', [])]
        
        old_servers = item.get('servers', [])
        item['servers'] = [s for s in old_servers if s.get('name', '') not in target_servers]
        item['servers'].insert(0, new_server)
        
        if new_downloads:
            item['downloadServers'] = new_downloads
        updated += 1
    
    print('Updated: {} items'.format(updated))
    
    if updated > 0:
        prefix = content[:content.index('[')]
        suffix = content[content.rindex(']') + 1:]
        json_str = json.dumps(data_js, ensure_ascii=False)
        with open('data.js', 'w', encoding='utf-8') as f:
            f.write(prefix + json_str + suffix)
        print('Saved data.js')
    
    final_remaining = sum(1 for item in data_js if any(s.get('name', '') in target_servers for s in item.get('servers', [])))
    print('Final remaining multi-quality servers: {}'.format(final_remaining))
