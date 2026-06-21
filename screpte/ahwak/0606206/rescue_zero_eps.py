#!/usr/bin/env python3
"""
Targeted rescue for series with 0 episodes.
Scrapes category pages to find watch URLs for zero-eps series,
then re-extracts episode data using the fixed regex.
"""
import sys, time, json, os, re, argparse
import undetected_chromedriver as uc
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = 'https://yam.ahwaktv.net'
CATEGORY_URL = BASE_URL + '/category.php?cat=moslslat-turkiaa-motrgma'
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
        except Exception as e:
            if a < max_retries - 1:
                print(f'    RETRY {a+1}: {str(e)[:60]}')
                time.sleep(5)
            else:
                print(f'    FAILED: {str(e)[:80]}')
                return False
    return False

def parse_category_page(html):
    items = []
    for item_html in re.finditer(
        r'<li class="col-xs-6 col-sm-4 col-md-3">.*?<a href="[^"]*(watch\.php\?vid=[^"]+)"[^>]*title="([^"]*)"',
        html, re.DOTALL
    ):
        vid_url = item_html.group(1)
        title = item_html.group(2)
        thumb_m = re.search(r'<img[^>]*src="([^"]*)"[^>]*alt="[^"]*"', item_html.group(0))
        thumb = thumb_m.group(1) if thumb_m else ''
        full_url = vid_url if vid_url.startswith('http') else BASE_URL + '/' + vid_url
        items.append({'title': title, 'url': full_url, 'thumb': thumb})
    return items

def extract_series_name(ep_title):
    name = re.sub(r'\s+الحلقة\s+\d+.*$', '', ep_title)
    name = re.sub(r'\s+(مترجمة|مدبلجة|HD|720p|1080p)\s*$', '', name)
    name = re.sub(r'\s+(مترجم|مدبلج)\s*$', '', name)
    name = name.strip()
    if not name.startswith('مسلسل') and not name.startswith('الموسم'):
        name = 'مسلسل ' + name
    return name

def parse_episode_page(html):
    info = {}
    m = re.search(r'<div class="pm-series-brief">.*?<img[^>]*src="([^"]*)"', html, re.DOTALL)
    if m:
        info['poster'] = m.group(1)
    m = re.search(r'<h1 class="title">([^<]+)</h1>', html)
    if m:
        info['series_name'] = m.group(1).strip()
    else:
        m = re.search(r'view-serie\.php\?name=([^"\'&]+)', html)
        if m:
            name = m.group(1).replace('-', ' ').replace('+', ' ')
            import urllib.parse
            info['series_name'] = urllib.parse.unquote(name).strip()
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

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=int, default=1, help='Start page')
    parser.add_argument('--end', type=int, default=50, help='End page')
    args = parser.parse_args()

    existing = json.load(open(DATA_PATH, 'r', encoding='utf-8'))
    zero_names = {s['name'] for s in existing if len(s.get('episodes', [])) == 0}
    print(f'Looking for {len(zero_names)} zero-eps series on pages {args.start}-{args.end}')

    driver = uc.Chrome(options=make_options(), version_main=148)
    driver.get(BASE_URL)
    time.sleep(15)

    found_series = {}
    found_names = set()
    for page in range(args.start, args.end + 1):
        # restart every 5 pages
        if page > args.start and (page - args.start) % 5 == 0:
            print(f'  Restarting browser...')
            try: driver.quit()
            except: pass
            driver = uc.Chrome(options=make_options(), version_main=148)
            driver.get(BASE_URL)
            time.sleep(15)
        url = f'{CATEGORY_URL}&page={page}&order=DESC'
        print(f'  Page {page}...', end=' ', flush=True)
        for attempt in range(3):
            try:
                if not safe_get(driver, url):
                    raise Exception('get failed')
                time.sleep(2)
                html = driver.page_source
                break
            except:
                if attempt < 2:
                    try: driver.quit()
                    except: pass
                    driver = uc.Chrome(options=make_options(), version_main=148)
                    driver.get(BASE_URL)
                    time.sleep(15)
                else:
                    html = ''
        if not html:
            print('SKIP')
            continue
        items = parse_category_page(html)
        for item in items:
            sname = extract_series_name(item['title'])
            if sname in zero_names and sname not in found_names:
                found_names.add(sname)
                found_series[sname] = item
        print(f'{len(items)} items, found {len(found_names)}/{len(zero_names)} zero-eps')
        if len(found_names) == len(zero_names):
            print('  All zero-eps series found!')
            break

    print(f'\nFound {len(found_series)} zero-eps series in pages {args.start}-{args.end}')

    if not found_series:
        print('Nothing to re-scrape.')
        driver.quit()
        return

    # Phase 2: re-scrape each found series
    print(f'\n{"="*60}')
    print(f'PHASE 2: Re-scraping episode data')
    print(f'{"="*60}')
    try: driver.quit()
    except: pass
    driver = uc.Chrome(options=make_options(), version_main=148)
    driver.get(BASE_URL)
    time.sleep(15)

    fixed_count = 0
    for idx, (sname, sinfo) in enumerate(found_series.items()):
        print(f'  [{idx+1}/{len(found_series)}] {sname[:50]}...', end=' ', flush=True)
        if not safe_get(driver, sinfo['url'], wait=5):
            print('TIMEOUT')
            continue
        html = driver.page_source
        info = parse_episode_page(html)
        if not info.get('series_name'):
            print('NO INFO')
            continue
        eps = info.get('episodes', [])
        print(f'{len(eps)} eps')

        # Update existing data
        for s in existing:
            if s['name'] == sname:
                s['episodes'] = eps
                if info.get('poster'):
                    s['poster'] = info['poster']
                if info.get('description'):
                    s['description'] = info['description']
                if info.get('series_url'):
                    s['series_url'] = info['series_url']
                if info.get('series_name') and sname != info['series_name']:
                    print(f'    Name change: "{sname}" -> "{info["series_name"]}"')
                break
        fixed_count += 1

        # Save after each
        with open(DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)

    # Stats
    zero_now = sum(1 for s in existing if len(s.get('episodes', [])) == 0)
    total_eps = sum(len(s.get('episodes', [])) for s in existing)
    print(f'\n{"="*60}')
    print(f'Fixed: {fixed_count}/{len(found_series)}')
    print(f'Remaining zero-eps: {zero_now}')
    print(f'Total episodes: {total_eps}')
    print(f'{"="*60}')
    driver.quit()

if __name__ == '__main__':
    main()
