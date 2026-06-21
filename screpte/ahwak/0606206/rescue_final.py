#!/usr/bin/env python3
"""Direct rescue for the last 3 zero-eps series."""
import sys, time, json, os, re, urllib.parse
import undetected_chromedriver as uc
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'https://yam.ahwaktv.net'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(SCRIPT_DIR, 'ahwaktv_data.json')

def make_options():
    o = uc.ChromeOptions()
    o.add_argument('--no-sandbox')
    o.add_argument('--window-size=1920,1080')
    return o

def safe_get(driver, url, max_retries=3, wait=8):
    for a in range(max_retries):
        try:
            driver.get(url)
            time.sleep(wait)
            return True
        except:
            if a < max_retries - 1:
                time.sleep(5)
            else:
                return False
    return False

def try_parse(html):
    info = {}
    m = re.search(r'<h1 class="title">([^<]+)</h1>', html)
    if m:
        info['series_name'] = m.group(1).strip()
    m = re.search(r'<div class="pm-series-brief">.*?<img[^>]*src="([^"]*)"', html, re.DOTALL)
    if m:
        info['poster'] = m.group(1)
    m = re.search(r'<div class="description">\s*<p>([^<]*)</p>', html, re.DOTALL)
    if m:
        info['description'] = m.group(1).strip()
    m = re.search(r'href=(["\'])[^"\']*(view-serie\.php\?name=[^"\']+)\1', html)
    if m:
        info['series_url'] = m.group(2)
    episodes = []
    for m in re.finditer(
        r'<a[^>]*title=(["\'])([^"\']+)\1[^>]*href=(["\'])(watch\.php\?vid=[^"\']+)\3[^>]*><em>(\d+)</em>',
        html
    ):
        ep_title = m.group(2)
        ep_vid = m.group(4)
        ep_num = int(m.group(5))
        ep_url = BASE_URL + '/' + ep_vid if not ep_vid.startswith('http') else ep_vid
        episodes.append({'number': ep_num, 'title': ep_title, 'url': ep_url, 'vid': ep_vid})
    if not episodes:
        for m in re.finditer(
            r'<a[^>]*title=(["\'])([^"\']+? الحلقة (\d+)[^"\']*)\1[^>]*href=(["\'])(watch\.php\?vid=[^"\']+)\4',
            html
        ):
            ep_title = m.group(2)
            ep_num = int(m.group(3))
            ep_vid = m.group(5)
            ep_url = BASE_URL + '/' + ep_vid if not ep_vid.startswith('http') else ep_vid
            episodes.append({'number': ep_num, 'title': ep_title, 'url': ep_url, 'vid': ep_vid})
    info['episodes'] = episodes
    return info

existing = json.load(open(DATA_PATH, 'r', encoding='utf-8'))
zero = [s for s in existing if len(s.get('episodes', [])) == 0]
print(f'Targeting {len(zero)} zero-eps series')

driver = uc.Chrome(options=make_options(), version_main=148)
driver.get(BASE_URL)
time.sleep(15)

for idx, s in enumerate(zero):
    name = s['name']
    url = s.get('series_url', '')
    print(f'\n[{idx+1}/{len(zero)}] {name}', end='')

    if not url:
        # Try to find it from category page
        print(f' (no URL, searching...)')
        cat_url = BASE_URL + '/category.php?cat=moslslat-turkiaa-motrgma&order=DESC'
        url_name = name.replace('مسلسل ', '').strip()
        search_url = BASE_URL + '/search.php?search=' + urllib.parse.quote(name.replace('مسلسل ', '').strip())
        print(f'  Searching: {search_url}')
        safe_get(driver, search_url, wait=5)
        html = driver.page_source
        m = re.search(r'<a[^>]*href="(watch\.php\?vid=[^"]+)"[^>]*title="([^"]*)"', html)
        if m:
            watch_url = m.group(1)
            if not watch_url.startswith('http'):
                watch_url = BASE_URL + '/' + watch_url
            url = watch_url
            print(f'  Found: {url}')
        else:
            print(f'  NOT FOUND via search, trying direct category scan')
            # Try a few pages
            found = False
            for page in [1, 2, 3, 4, 5, 101, 102, 103, 110, 111, 115, 120, 125, 130]:
                if found:
                    break
                page_url = f'{BASE_URL}/category.php?cat=moslslat-turkiaa-motrgma&page={page}&order=DESC'
                safe_get(driver, page_url, wait=4)
                html = driver.page_source
                for item in re.finditer(r'<a href="[^"]*(watch\.php\?vid=[^"]+)"[^>]*title="([^"]*)"', html):
                    title = item.group(2)
                    # Check if this title matches the series name
                    clean_title = re.sub(r'\s+الحلقة\s+\d+.*$', '', title).strip()
                    if clean_title == name.replace('مسلسل ', '').strip():
                        watch_url = item.group(1)
                        if not watch_url.startswith('http'):
                            watch_url = BASE_URL + '/' + watch_url
                        url = watch_url
                        print(f'  Found on page {page}: {url}')
                        found = True
                        break
            if not found:
                print(f'  SKIP - could not find')
                continue

    # Now visit the page and extract episodes
    print(f'\n  Visiting: {url[:80]}')
    if not safe_get(driver, url, wait=6):
        print(f'  TIMEOUT')
        continue
    html = driver.page_source
    info = try_parse(html)

    if info.get('series_name'):
        print(f'  Name: {info["series_name"]}')
    print(f'  Episodes: {len(info["episodes"])}')

    # Update data
    for ex in existing:
        if ex['name'] == name:
            if info['episodes']:
                ex['episodes'] = info['episodes']
            if info.get('poster'):
                ex['poster'] = info['poster']
            if info.get('description'):
                ex['description'] = info['description']
            if info.get('series_url'):
                ex['series_url'] = info['series_url']
            break

    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f'  Saved')

driver.quit()

zero_after = sum(1 for s in existing if len(s.get('episodes', [])) == 0)
print(f'\nRemaining zero-eps: {zero_after}')
print(f'Total episodes: {sum(len(s.get("episodes",[])) for s in existing)}')
