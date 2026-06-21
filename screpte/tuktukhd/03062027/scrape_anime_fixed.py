import requests, re, json, concurrent.futures, base64, html

headers = {'User-Agent': 'Mozilla/5.0'}
CATEGORY = 'https://tuktukhd.com/category/anime-6/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d9%86%d9%85%d9%8a'

OUTPUT_FILE = 'scripts/tuktukhd/data/results_anime.json'

def scrape_listing(url):
    try:
        r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        if r.status_code != 200:
            return []
        items = re.findall(
            r'<a[^>]*href="(https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+)"[^>]*>.*?<img[^>]*alt="([^"]+)"[^>]*>.*?</a>',
            r.text, re.DOTALL
        )
        results = []
        for href, alt in items:
            alt = alt.strip()
            # Match: فيلم NAME YEAR مترجم اون لاين
            m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم(?:\s+اون\s+لاين)?', alt)
            if not m:
                # Match: فيلم YEAR NAME مترجم اون لاين
                m = re.match(r'فيلم\s+(\d{4})\s+(.+?)\s+مترجم(?:\s+اون\s+لاين)?', alt)
                if m:
                    name = m.group(2).strip()
                    year = m.group(1)
                else:
                    continue
            else:
                name = m.group(1).strip()
                year = m.group(2)
            name = html.unescape(name)
            results.append({'name': name, 'year': year, 'url': href})
        return results
    except:
        return []

# Step 1: Scrape ALL pages sequentially until empty
print('Scraping anime category pages (sequential)...')
all_index = []
for page in range(1, 50):
    url = '{}/page/{}/'.format(CATEGORY, page) if page > 1 else CATEGORY + '/'
    entries = scrape_listing(url)
    if not entries:
        print('Page {}: empty, stopping'.format(page))
        break
    all_index.extend(entries)
    print('  Page {}: {} (total: {})'.format(page, len(entries), len(all_index)))

# Dedup
seen_urls = set()
deduped = []
for m in all_index:
    if m['url'] not in seen_urls:
        seen_urls.add(m['url'])
        deduped.append(m)

print('Total index: {} (deduped: {})'.format(len(all_index), len(deduped)))

# Save index for reference
with open('scripts/tuktukhd/data/tuktuk_anime_index_v3.json', 'w', encoding='utf-8') as f:
    json.dump(deduped, f, ensure_ascii=False, indent=2)

# Step 2: Visit each page and extract details
def extract_details(text):
    details = {}
    crypts = re.findall(r'data-crypt="([^"]+)"', text)
    watch_urls = []
    for c in crypts:
        try:
            watch_urls.append(base64.b64decode(c).decode('utf-8'))
        except:
            pass
    dl_links = re.findall(r'data-real-url="([^"]+)"', text)
    si = re.findall(r'<li[^>]*class="[^"]*server--item[^"]*"[^>]*>.*?<span>([^<]*)</span>', text, re.DOTALL)
    poster = ''
    pm = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', text)
    if pm:
        poster = pm.group(1)
    if not poster:
        pm = re.search(r'class="[^"]*poster[^"]*"[^>]*src="([^"]+)"', text)
        if pm:
            poster = pm.group(1)
    desc = ''
    dm = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', text)
    if dm:
        desc = dm.group(1)
    if not desc:
        dm = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', text)
        if dm:
            desc = dm.group(1)
    detail_labels = {
        'توقيت الفيلم': 'توقيت الفيلم :',
        'جودة الفيلم': 'جودة الفيلم :',
        'بطولة': 'بطولة :',
        'المخرجين': 'المخرجين :',
        'المؤلفين': 'المؤلفين :',
        'دولة الفيلم': 'دولة الفيلم :',
        'لغة الفيلم': 'لغة الفيلم :',
        'العمر': 'العمر :',
    }
    for label_key, label_text in detail_labels.items():
        m = re.search(r'<span>' + re.escape(label_text) + r'\s*</span>\s*<strong>([^<]+)</strong>', text)
        if m:
            details[label_key] = m.group(1).strip()
    cast_m = re.search(r'<span>بطولة\s*:\s*</span>(.*?)</li>', text, re.DOTALL)
    if cast_m:
        cast_links = re.findall(r'<a[^>]*>([^<]+)</a>', cast_m.group(1))
        if cast_links:
            details['بطولة :'] = '، '.join(c.strip() for c in cast_links)
    dir_m = re.search(r'<span>المخرجين\s*:\s*</span>(.*?)</li>', text, re.DOTALL)
    if dir_m:
        dir_links = re.findall(r'<a[^>]*>([^<]+)</a>', dir_m.group(1))
        if dir_links:
            details['المخرجين :'] = '، '.join(d.strip() for d in dir_links)
    # Actual category
    actual_cats = []
    cm = re.search(r'التصنيفات\s*</span>\s*<a[^>]*>([^<]+)</a>', text)
    if cm:
        actual_cats.append(cm.group(1).strip())
    return {
        'watch_urls': watch_urls,
        'dl_links': dl_links,
        'server_name': si[0].strip() if si else 'TukTuk Vip',
        'poster': poster,
        'desc': desc,
        'details': details,
        'category': actual_cats,
    }

def extract(m):
    try:
        r = requests.get(m['url'], timeout=20, headers=headers)
        info = extract_details(r.text)
        if not info['watch_urls']:
            return {'title': m['name'], 'category': info['category'], 'success': False}
        titre = 'فيلم {} {} مترجم اون لاين'.format(m['name'], m['year'])
        video_url = info['watch_urls'][0]
        watch_servers = []
        for i, wu in enumerate(info['watch_urls']):
            sname = info['server_name'] if i == 0 else 'TukTuk {}'.format(i + 1)
            watch_servers.append({
                'name': sname,
                'url': wu,
                'isDefault': i == 0
            })
        download_servers = []
        for dl in info['dl_links']:
            download_servers.append({
                'name': 'Download',
                'url': dl
            })
        det = info['details']
        details_dict = {}
        if 'توقيت الفيلم' in det and det['توقيت الفيلم'].strip():
            details_dict['توقيت الفيلم :'] = det['توقيت الفيلم'].strip()
        if 'جودة الفيلم' in det and det['جودة الفيلم'].strip():
            details_dict['جودة الفيلم :'] = det['جودة الفيلم'].strip()
        if 'بطولة :' in det:
            details_dict['بطولة :'] = det['بطولة :']
        if 'المخرجين :' in det:
            details_dict['المخرجين :'] = det['المخرجين :']
        details_dict['موعد الصدور :'] = m['year']
        return {
            'titre': titre,
            'image': info['poster'],
            'video_url': video_url,
            'servers': {
                'watch': watch_servers,
                'download': download_servers
            },
            'info': {
                'story': info['desc'],
                'catssection': info['category'],
                'details': details_dict
            },
            'category': info['category'],
            'success': True
        }
    except:
        return {'title': m['name'], 'success': False}

print('Visiting {} movie pages...'.format(len(deduped)))
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    futures = [ex.submit(extract, m) for m in deduped]
    for i, future in enumerate(concurrent.futures.as_completed(futures)):
        results.append(future.result())
        if (i + 1) % 30 == 0 or i + 1 == len(deduped):
            print('  {}/{}'.format(i + 1, len(deduped)))

successful = [r for r in results if r.get('success')]
failed = [r for r in results if not r.get('success')]
print('Success: {}, Failed: {}'.format(len(successful), len(failed)))

# Category distribution
from collections import Counter
cat_dist = Counter()
for r in successful:
    for c in (r.get('category') or []):
        cat_dist[c] += 1
print('\nCategory distribution:')
for cat, count in cat_dist.most_common():
    print('  {}: {}'.format(cat, count))

# Filter to anime only
anime_only = [r for r in successful if any('انمي' in (c or '') for c in (r.get('category') or []))]
print('\nAnime movies: {}'.format(len(anime_only)))
non_anime = len(successful) - len(anime_only)
print('Non-anime excluded: {}'.format(non_anime))

output = []
for r in anime_only:
    entry = {k: v for k, v in r.items() if k not in ('success', 'category')}
    output.append(entry)

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print('\nSaved {} anime movies to {}'.format(len(output), OUTPUT_FILE))
