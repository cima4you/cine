import requests, re, base64, json

headers = {'User-Agent': 'Mozilla/5.0'}
FILM_PATTERN = r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+'

CAT_LABEL_MAP = {
    'افلام اجنبي': 'أجنبي',
    'افلام هندي': 'هندي',
    'افلام اسيوي': 'أسيوي',
    'افلام تركي': 'تركي',
    'افلام مدبلجة': 'مدبلج',
    'افلام انمي': 'أنمي',
}

PRIORITY = ['تركي', 'مدبلج', 'أنمي', 'نتفليكس', 'أسيوي', 'هندي', 'أجنبي']

def classify_from_catssection(html):
    cs = re.search(r'class="catssection"[^>]*>(.*?)</section>', html, re.DOTALL)
    if not cs:
        cs = re.search(r'<span>التصنيفات</span>(.*?)</li>', html, re.DOTALL)
    if not cs:
        return 'أجنبي'
    content = cs.group(1)
    cat_labels = re.findall(r'<a[^>]*>([^<]+)</a>', content)
    found_types = set()
    if 'film-netflix' in content:
        found_types.add('نتفليكس')
    for label in cat_labels:
        label = label.strip()
        if label in CAT_LABEL_MAP:
            found_types.add(CAT_LABEL_MAP[label])
    if not found_types:
        return 'أجنبي'
    for p in PRIORITY:
        if p in found_types:
            return p
    return 'أجنبي'

# Test Phase 1
BASE_URL = 'https://tuktukhd.com/category/movies-2/'
all_listings = []
for page in range(1, 4):
    url = '{}page/{}/'.format(BASE_URL, page) if page > 1 else BASE_URL
    r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
    text = r.content.decode('utf-8')
    hrefs = re.findall(FILM_PATTERN, text, re.IGNORECASE)
    alts = re.findall(r'alt="([^"]+)"', text)
    for alt, href in zip(alts[:len(hrefs)], hrefs):
        alt = alt.strip()
        if alt == 'توك توك سينما':
            continue
        m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+(?:مترجم|مدبلج)', alt)
        if m:
            all_listings.append({'name': m.group(1).strip(), 'year': m.group(2), 'url': href})

print('Listings:', len(all_listings))

# Test Phase 2 for first 3
for m in all_listings[:3]:
    print('\nMovie:', m['name'][:40], m['year'])
    print('URL:', m['url'][:80])
    try:
        r = requests.get(m['url'], timeout=20, headers=headers)
        html = r.content.decode('utf-8')
        
        # Check if series
        has_seasons = bool(re.search(r'class="[^"]*seasons[^"]*"', html))
        has_episodes = bool(re.search(r'class="[^"]*episodes[^"]*"', html))
        print('  series check: seasons={}, episodes={}'.format(has_seasons, has_episodes))
        
        # Extract watch URLs
        crypts = re.findall(r'data-crypt="([^"]+)"', html)
        watch_urls = []
        for c in crypts:
            try:
                watch_urls.append(base64.b64decode(c).decode('utf-8'))
            except:
                pass
        print('  watch_urls:', len(watch_urls))
        if not watch_urls:
            print('  SKIP: no watch urls')
            continue
        
        # Classify
        detected_type = classify_from_catssection(html)
        print('  type:', detected_type)
        
        # Build result
        dl_links = re.findall(r'data-real-url="([^"]+)"', html)
        si = re.findall(r'<li[^>]*class="[^"]*server--item[^"]*"[^>]*>.*?<span>([^<]*)</span>', html, re.DOTALL)
        poster = ''
        pm = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
        if pm:
            poster = pm.group(1)
        if not poster:
            pm = re.search(r'class="[^"]*poster[^"]*"[^>]*src="([^"]+)"', html)
            if pm:
                poster = pm.group(1)
        
        watch_servers = []
        for i, wu in enumerate(watch_urls):
            sname = si[i].strip() if i < len(si) else ('TukTuk Vip' if i == 0 else 'TukTuk {}'.format(i + 1))
            watch_servers.append({'name': sname, 'url': wu, 'isDefault': i == 0})
        
        result = {
            'video_url': watch_servers[0]['url'],
            'image': poster,
            'type': detected_type,
        }
        print('  SUCCESS:', result['video_url'][:40])
        
    except Exception as e:
        print('  ERROR:', type(e).__name__, str(e))
        import traceback
        traceback.print_exc()
