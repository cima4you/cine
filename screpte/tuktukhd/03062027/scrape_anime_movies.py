import requests, re, json, concurrent.futures, base64, sys, time, html

headers = {'User-Agent': 'Mozilla/5.0'}
CATEGORY = 'https://tuktukhd.com/category/anime-6/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d9%86%d9%85%d9%8a'
# FILM_PATTERN replaced by inline regex in scrape_listing

OUTPUT_FILE = 'scripts/tuktukhd/data/results_anime.json'

start_page = int(sys.argv[1]) if len(sys.argv) > 1 else 1
end_page = int(sys.argv[2]) if len(sys.argv) > 2 else 999

print('Scraping Anime pages {} to {}'.format(start_page, end_page))

def scrape_listing(url):
    try:
        r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        if r.status_code != 200:
            return []
        # Extract <a href="..."><img alt="فيلم ..."></a> pairs (avoids misalignment)
        items = re.findall(
            r'<a[^>]*href="(https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+)"[^>]*>.*?<img[^>]*alt="(\u0641\u064A\u0644\u0645[^"]+)"[^>]*>.*?</a>',
            r.text, re.DOTALL
        )
        results = []
        for href, alt in items:
            alt = alt.strip()
            m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم(?:\s+اون\s+لاين)?', alt)
            if m:
                name = m.group(1).strip()
                year = m.group(2)
                name = html.unescape(name)
                results.append({'name': name, 'year': year, 'url': href})
        return results
    except:
        return []

all_listed = []
for page in range(start_page, end_page + 1):
    url = '{}page/{}/'.format(CATEGORY, page) if page > 1 else CATEGORY
    entries = scrape_listing(url)
    if not entries and page > start_page:
        print('  Page {}: empty, stopping'.format(page))
        break
    all_listed.extend(entries)
    print('  Page {}: {} entries (total: {})'.format(page, len(entries), len(all_listed)))

# Deduplicate by URL
seen_urls = set()
deduped = []
for m in all_listed:
    if m['url'] not in seen_urls:
        seen_urls.add(m['url'])
        deduped.append(m)

print('Total scraped: {} (after dedup: {})'.format(len(all_listed), len(deduped)))
if not deduped:
    print('No entries found!')
    sys.exit(0)

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
    cats = []
    seen_cats = set()
    breadcrumb = re.findall(r'<a[^>]*href="[^"]*category[^"]*"[^>]*>([^<]+)</a>', text)
    for c in breadcrumb:
        c = c.strip()
        if c and c not in ('الرئيسية', 'الأفلام', 'جميع الافلام', 'الحلقات', 'جميع الحلقات') and c not in seen_cats:
            cats.append(c)
            seen_cats.add(c)
    return {
        'watch_urls': watch_urls,
        'dl_links': dl_links,
        'server_name': si[0].strip() if si else 'TukTuk Vip',
        'poster': poster,
        'desc': desc,
        'details': details,
        'categories': cats,
    }

def extract(m):
    try:
        r = requests.get(m['url'], timeout=20, headers=headers)
        info = extract_details(r.text)
        if not info['watch_urls']:
            return {'title': m['name'], 'success': False}
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
                'catssection': info['categories'],
                'details': details_dict
            },
            'success': True
        }
    except Exception as e:
        return {'title': m['name'], 'success': False}

print('Visiting {} pages...'.format(len(deduped)))
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    futures = [ex.submit(extract, m) for m in deduped]
    for i, future in enumerate(concurrent.futures.as_completed(futures)):
        results.append(future.result())
        if (i + 1) % 20 == 0 or i + 1 == len(deduped):
            print('  {}/{}'.format(i + 1, len(deduped)))

successful = [r for r in results if r.get('success')]
failed = [r for r in results if not r.get('success')]
print('Success: {}, Failed: {}'.format(len(successful), len(failed)))

output = []
for r in successful:
    entry = {k: v for k, v in r.items() if k != 'success'}
    output.append(entry)

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print('\nSaved {} movies to {}'.format(len(output), OUTPUT_FILE))
print('Format matches results_foreign.json (titre, image, video_url, servers, info)')

# Also save an index for reference
index_out = 'scripts/tuktukhd/data/tuktuk_anime_index.json'
index_data = [{'name': m['name'], 'year': m['year'], 'url': m['url']} for m in deduped]
with open(index_out, 'w', encoding='utf-8') as f:
    json.dump(index_data, f, ensure_ascii=False, indent=2)
print('Saved index to {}'.format(index_out))
