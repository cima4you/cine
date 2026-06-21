import requests, re, base64
headers = {'User-Agent': 'Mozilla/5.0'}
FILM_PATTERN = r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+'

# Get first 5 movies from page 1
url = 'https://tuktukhd.com/category/movies-2/'
r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
text = r.content.decode('utf-8')
hrefs = re.findall(FILM_PATTERN, text, re.IGNORECASE)
alts = re.findall(r'alt="([^"]+)"', text)

count = 0
for alt, href in zip(alts[:len(hrefs)], hrefs):
    alt = alt.strip()
    if alt == 'توك توك سينما':
        continue
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+(?:مترجم|مدبلج)', alt)
    if m and count < 5:
        count += 1
        name, year = m.group(1).strip(), m.group(2)
        print('Movie {}: {} ({})'.format(count, name[:40], year))
        print('  URL: {}'.format(href[:70]))
        
        try:
            r2 = requests.get(href, timeout=20, headers=headers)
            html = r2.content.decode('utf-8')
            
            # Check watch URLs
            crypts = re.findall(r'data-crypt="([^"]+)"', html)
            watch_urls = []
            for c in crypts:
                try:
                    watch_urls.append(base64.b64decode(c).decode('utf-8'))
                except:
                    pass
            print('  watch_urls: {}'.format(len(watch_urls)))
            
            if not watch_urls:
                print('  SKIP: no watch urls')
                continue
            
            # Check seasons
            has_seasons = bool(re.search(r'class="[^"]*seasons[^"]*"', html))
            has_episodes = bool(re.search(r'class="[^"]*episodes[^"]*"', html))
            print('  seasons: {}, episodes: {}'.format(has_seasons, has_episodes))
            
            if has_seasons or has_episodes:
                print('  SKIP: is series')
                continue
            
            # Classify
            cs = re.search(r'class="catssection"[^>]*>(.*?)</section>', html, re.DOTALL)
            if cs:
                cat_links = re.findall(r'<a[^>]*href="([^"]*category[^"]*)"[^>]*>([^<]+)</a>', cs.group(1))
                print('  cats: {}'.format([l for _, l in cat_links]))
            else:
                print('  NO catssection')
            
            print('  SUCCESS')
        except Exception as e:
            print('  ERROR: {}'.format(e))

# Also check page 2 first movie
print('\n--- Page 2 first movie ---')
url2 = 'https://tuktukhd.com/category/movies-2/page/2/'
r2 = requests.get(url2, timeout=15, headers=headers, allow_redirects=True)
text2 = r2.content.decode('utf-8')
hrefs2 = re.findall(FILM_PATTERN, text2, re.IGNORECASE)
alts2 = re.findall(r'alt="([^"]+)"', text2)

for alt, href in zip(alts2[:len(hrefs2)], hrefs2):
    alt = alt.strip()
    if alt == 'توك توك سينما':
        continue
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+(?:مترجم|مدبلج)', alt)
    if m:
        print('Movie: {} ({})'.format(m.group(1).strip()[:40], m.group(2)))
        print('  URL: {}'.format(href[:70]))
        
        try:
            r3 = requests.get(href, timeout=20, headers=headers)
            html = r3.content.decode('utf-8')
            crypts = re.findall(r'data-crypt="([^"]+)"', html)
            watch_urls = []
            for c in crypts:
                try:
                    watch_urls.append(base64.b64decode(c).decode('utf-8'))
                except:
                    pass
            print('  watch_urls: {}'.format(len(watch_urls)))
            if watch_urls:
                print('  SUCCESS')
            else:
                print('  SKIP: no watch urls')
        except Exception as e:
            print('  ERROR: {}'.format(e))
        break
