import requests, re, json, concurrent.futures, base64, sys, os

headers = {'User-Agent': 'Mozilla/5.0'}
CATEGORY = 'https://tuktukhd.com/channel/film-netflix-1'
FILM_PATTERN = r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+'

start_page = int(sys.argv[1]) if len(sys.argv) > 1 else 1
end_page = int(sys.argv[2]) if len(sys.argv) > 2 else 999

print('Scraping Netflix category pages {} to {}...'.format(start_page, end_page))

all_listed = []
for page in range(start_page, end_page + 1):
    url = '{}page/{}/'.format(CATEGORY, page) if page > 1 else CATEGORY
    try:
        r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        if r.status_code != 200:
            print('  Page {}: status {}'.format(page, r.status_code))
            if page > 1:
                break
            continue
        text = r.content.decode('utf-8')
        alts = re.findall(r'alt="([^"]+)"', text)
        hrefs = re.findall(FILM_PATTERN, text, re.IGNORECASE)
        entries = []
        for alt, href in zip(alts[:len(hrefs)], hrefs):
            alt = alt.strip()
            m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+(?:مترجم|مدبلج)', alt)
            if m:
                entries.append({'name': m.group(1).strip(), 'year': m.group(2), 'url': href})
        if not entries:
            print('  Page {}: 0 entries - stopping'.format(page))
            break
        all_listed.extend(entries)
        print('  Page {}: {} (total: {})'.format(page, len(entries), len(all_listed)))
    except Exception as e:
        print('  Page {} error: {}'.format(page, e))
        break

print('Total scraped from listing: {}'.format(len(all_listed)))
if not all_listed:
    sys.exit(0)

# Deduplicate by url
seen_urls = set()
unique_listed = []
for m in all_listed:
    if m['url'] not in seen_urls:
        seen_urls.add(m['url'])
        unique_listed.append(m)
print('Unique: {}'.format(len(unique_listed)))

# Load data.js for duplicate check
with open('data.js', 'r', encoding='utf-8') as f:
    content = f.read()
start = content.index('[')
end = content.rindex(']') + 1
data_js = json.loads(content[start:end])

def norm(t):
    t = t.lower().strip()
    t = re.sub(r"[`'’‘:.,!?&/\-]", '', t)
    t = re.sub(r'\s+', '', t)
    return t

existing = set()
for item in data_js:
    existing.add((norm(item.get('title', '')), str(item.get('year', ''))))

new_movies = []
for m in unique_listed:
    key = (norm(m['name']), m['year'])
    if key not in existing:
        new_movies.append(m)
        existing.add(key)

print('New (not in data.js): {}'.format(len(new_movies)))
if not new_movies:
    print('No new movies to scrape.')
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
        if c and c not in ('الرئيسية', 'الأفلام', 'جميع الافلام', 'الحلقات', 'جميع الحلقات', 'مسلسلات') and c not in seen_cats:
            cats.append(c)
            seen_cats.add(c)
    return {
        'watch_urls': watch_urls,
        'dl_links': dl_links,
        'server_names': [s.strip() for s in si],
        'poster': poster,
        'desc': desc,
        'details': details,
        'categories': cats,
    }

def extract(m):
    try:
        r = requests.get(m['url'], timeout=20, headers=headers)
        info = extract_details(r.content.decode('utf-8'))
        if not info['watch_urls']:
            return {'title': m['name'], 'success': False}
        titre = 'فيلم {} {} مترجم اون لاين'.format(m['name'], m['year'])
        video_url = info['watch_urls'][0]
        watch_servers = []
        for i, wu in enumerate(info['watch_urls']):
            sname = info['server_names'][i] if i < len(info['server_names']) else ('TukTuk Vip' if i == 0 else 'TukTuk {}'.format(i + 1))
            watch_servers.append({'name': sname, 'url': wu, 'isDefault': i == 0})
        download_servers = []
        for dl in info['dl_links']:
            download_servers.append({'name': 'Download', 'url': dl})
        det = info['details']
        details_dict = {}
        for k in ['توقيت الفيلم :', 'جودة الفيلم :', 'بطولة :', 'المخرجين :', 'دولة الفيلم :', 'لغة الفيلم :']:
            v = det.get(k, '')
            if v and v.strip():
                details_dict[k] = v.strip()
        details_dict['موعد الصدور :'] = m['year']
        return {
            'titre': titre,
            'image': info['poster'],
            'video_url': video_url,
            'servers': {'watch': watch_servers, 'download': download_servers},
            'info': {'story': info['desc'], 'catssection': info['categories'], 'details': details_dict},
            'success': True
        }
    except Exception as e:
        return {'title': m['name'], 'success': False}

print('Visiting {} pages...'.format(len(new_movies)))
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    futures = [ex.submit(extract, m) for m in new_movies]
    for i, future in enumerate(concurrent.futures.as_completed(futures)):
        results.append(future.result())
        if (i + 1) % 20 == 0 or i + 1 == len(new_movies):
            print('  {}/{}'.format(i + 1, len(new_movies)))

successful = [r for r in results if r.get('success')]
failed = [r for r in results if not r.get('success')]
print('Success: {}, Failed: {}'.format(len(successful), len(failed)))

output = [{k: v for k, v in r.items() if k != 'success'} for r in successful]

out_file = 'scripts/tuktukhd/data/results_netflix.json'
with open(out_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print('Saved {} movies to {}'.format(len(output), out_file))
