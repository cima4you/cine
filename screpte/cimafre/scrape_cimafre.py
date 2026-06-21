import requests, re, json, os, time, argparse
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = 'https://cimafre.site'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
}
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
MOVIES_FILE = os.path.join(DATA_DIR, 'arabic_movies.json')

session = requests.Session()
session.headers.update(HEADERS)

def fetch(url):
    for attempt in range(3):
        try:
            r = session.get(url, timeout=30)
            r.encoding = 'utf-8'
            if r.status_code == 200:
                return r
        except:
            time.sleep(2)
    return None

def scrape_page(cat, page):
    url = f'{BASE}/category.php?cat={cat}&page={page}&order=DESC'
    r = fetch(url)
    if not r:
        return []
    soup = BeautifulSoup(r.text, 'html.parser')
    movies = []
    for li in soup.select('li.col-xs-6'):
        thumb = li.select_one('.pm-video-thumb')
        if not thumb:
            continue
        link = thumb.select_one('a[href*="watch.php"]')
        if not link:
            continue
        m = re.search(r'vid=([a-f0-9]+)', link['href'])
        if not m:
            continue
        img = thumb.select_one('img')
        dur = thumb.select_one('.pm-label-duration')
        movies.append({
            'vid': m.group(1),
            'title': link.get('title', '') or link.text.strip(),
            'thumb': img.get('src', '') if img else '',
            'duration': dur.text.strip() if dur else '',
            'page': page,
        })
    return movies

def get_servers(vid):
    r = fetch(f'{BASE}/play.php?vid={vid}')
    if not r:
        return [], []
    t = r.text
    watch = re.findall(
        r'<li[^>]*data-embed-id="(\d+)"[^>]*data-embed-url="([^"]+)"[^>]*>.*?<strong>(.*?)</strong>',
        t, re.DOTALL
    )
    download = re.findall(
        r'<li[^>]*data-download-url="([^"]+)"[^>]*>.*?<strong>(.*?)</strong>',
        t, re.DOTALL
    )
    watch_servers = [{'id': int(s[0]), 'name': s[2].strip(), 'url': s[1]} for s in watch]
    down_servers = [{'name': d[1].strip(), 'url': d[0]} for d in download]
    return watch_servers, down_servers

def get_detail(vid):
    r = fetch(f'{BASE}/watch.php?vid={vid}')
    if not r:
        return {}
    data = {}
    m = re.search(r'var pm_video_data\s*=\s*({.*?});', r.text, re.DOTALL)
    if m:
        pm = m.group(1)
        for f in ['duration_str', 'category_str', 'thumb_url']:
            fm = re.search(rf'{f}\s*:\s*"([^"]*)"', pm)
            if fm:
                data[f] = fm.group(1)
    soup = BeautifulSoup(r.text, 'html.parser')
    h1 = soup.select_one('h1')
    if h1:
        data['h1_title'] = h1.text.strip()
    desc = soup.select_one('.am-video-description')
    if desc:
        data['description'] = desc.text.strip()[:500]
    return data


def main():
    parser = argparse.ArgumentParser(description='سحب أفلام عربية من cimafre.site')
    parser.add_argument('--from', dest='page_from', type=int, default=1, help='صفحة البداية')
    parser.add_argument('--to', dest='page_to', type=int, default=999, help='صفحة النهاية')
    parser.add_argument('--servers', action='store_true', help='جلب السيرفرات فقط')
    parser.add_argument('--parallel', type=int, default=5, help='عدد الطلبات المتزامنة')
    args = parser.parse_args()

    movies = json.load(open(MOVIES_FILE, 'r', encoding='utf-8')) if os.path.exists(MOVIES_FILE) else []

    if not args.servers:
        existing = {m['vid'] for m in movies}
        for page in range(args.page_from, args.page_to + 1):
            print(f'صفحة {page}...')
            page_movies = scrape_page('arabic-moives', page)
            if not page_movies:
                print('  (انتهت الصفحات)')
                break
            new = [m for m in page_movies if m['vid'] not in existing]
            movies.extend(new)
            existing |= {m['vid'] for m in new}
            print(f'  {len(new)} جديد (المجموع {len(movies)})')
            if page % 10 == 0:
                json.dump(movies, open(MOVIES_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
            time.sleep(0.5)
        json.dump(movies, open(MOVIES_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'\nتم الحفظ: {len(movies)} فيلم')

    need_servers = [m for m in movies if not m.get('servers')]
    if need_servers:
        print(f'\nجلب السيرفرات لـ {len(need_servers)} فيلم...')
        def process(movie):
            watch, download = get_servers(movie['vid'])
            if watch:
                movie['servers'] = watch
            if download:
                movie['downloads'] = download
            return movie['vid'], len(watch)

        with ThreadPoolExecutor(max_workers=args.parallel) as ex:
            futures = [ex.submit(process, m) for m in need_servers]
            done = 0
            for f in as_completed(futures):
                done += 1
                if done % 25 == 0:
                    json.dump(movies, open(MOVIES_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
                    sv = len([x for x in movies if x.get('servers')])
                    print(f'  {done}/{len(need_servers)} - {sv} مع سيرفرات')

        json.dump(movies, open(MOVIES_FILE, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        sv = len([x for x in movies if x.get('servers')])
        total_servers = sum(len(x.get('servers', [])) for x in movies if x.get('servers'))
        print(f'تم: {sv}/{len(movies)} مع سيرفرات (إجمالي {total_servers} سيرفر)')

if __name__ == '__main__':
    main()
