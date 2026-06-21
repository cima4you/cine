#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكربت سحب أفلام أجنبية من TopCinema (web.topcinemaa.com)
الاستعمال:
  python scripts/topcinema/scrape_topcinema_movies.py --start 1 --end 5 --workers 4
  python scripts/topcinema/scrape_topcinema_movies.py --resume
  python scripts/topcinema/scrape_topcinema_movies.py --convert
"""
import os, sys, re, json, time, argparse, copy, html as html_mod, threading
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = __import__('io').TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = __import__('io').TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import requests

CAT_URL = 'https://web.topcinemaa.com/category/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D8%A7%D8%AC%D9%86%D8%A8%D9%8A-8/'
AJAX_URL = 'https://web.topcinemaa.com/wp-content/themes/movies2023/Ajaxat/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
    'Referer': 'https://web.topcinemaa.com/',
}

_thread_local = threading.local()
def get_session():
    if not hasattr(_thread_local, 'sess'):
        sess = requests.Session()
        sess.headers.update(HEADERS)
        _thread_local.sess = sess
    return _thread_local.sess
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
OUTPUT_DIR = os.path.join(SCRIPT_DIR, '..', '..')
OUTPUT_FILE = os.path.normpath(os.path.join(OUTPUT_DIR, 'توب سينما أفلام أجنبية.js'))

def p(text):
    try: print(text, flush=True)
    except: print(repr(text), flush=True)

def fetch(url, **kwargs):
    ses = get_session()
    for attempt in range(5):
        try:
            r = ses.get(url, timeout=30, **kwargs)
            r.raise_for_status()
            return r
        except Exception as e:
            if '429' in str(e) and attempt < 4:
                time.sleep(3 * (attempt + 1))
                continue
            if attempt < 4:
                time.sleep(2)
                continue
            raise

def fetch_text(url, **kwargs):
    return fetch(url, **kwargs).text

def save_json(path, data):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

def load_json(path):
    if not os.path.exists(path):
        return [] if 'listing' in path else {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_en_title(html_title):
    """
    استخراج اسم الفلم باللغة الأجنبية من النص مثل:
    "فيلم Colors of Evil: Black 2026 مترجم اون لاين"
    """
    if not html_title:
        return ''
    clean = html_title.strip()
    clean = html_mod.unescape(clean)
    clean = re.sub(r'^فيلم\s+', '', clean).strip()
    clean = re.sub(r'\s+مترجم\s*اون\s*لاين\s*$', '', clean).strip()
    clean = re.sub(r'\s+مترجم\s*$', '', clean).strip()
    clean = re.sub(r'\s+اون\s*لاين\s*$', '', clean).strip()
    clean = re.sub(r'\s+\d{4}\s*$', '', clean).strip()
    return clean.strip()

def extract_year_from_title(html_title):
    ym = re.search(r'(\d{4})', html_title)
    return ym.group(1) if ym else ''

def listing_page(page):
    url = f'{CAT_URL}page/{page}/' if page > 1 else CAT_URL
    html = fetch_text(url)
    items = []

    # Extract each Small--Box directly from the full HTML
    # Find the start of the movie listing section
    # Look for the container that holds all movie cards
    start_markers = ['<ul class="Posts--List SixInRow">', '<div class="filterPosts">']
    container = html
    for marker in start_markers:
        pos = html.find(marker)
        if pos != -1:
            container = html[pos:]
            break

    # Extract each Small--Box by finding consecutive divs
    idx = 0
    while True:
        pos = container.find('<div class="Small--Box">', idx)
        if pos == -1:
            break
        # Find the next Small--Box to determine the boundary
        next_pos = container.find('<div class="Small--Box">', pos + len('<div class="Small--Box">'))
        if next_pos == -1:
            # Last card - extract a reasonable chunk
            card_html = container[pos:pos + 1200]
        else:
            card_html = container[pos:next_pos]

        try:
            href_m = re.search(r'href="(https://web\.topcinemaa\.com/[^"]+)"', card_html)
            if not href_m:
                idx = pos + 1
                continue
            url = href_m.group(1)

            title = ''
            alt_m = re.search(r'alt="([^"]+)"', card_html)
            if alt_m:
                title = extract_en_title(alt_m.group(1))
            if not title:
                h3_m = re.search(r'<h3[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</h3>', card_html, re.DOTALL)
                if h3_m:
                    title = extract_en_title(re.sub(r'<[^>]+>', '', h3_m.group(1)).strip())

            poster = ''
            poster_m = re.search(r'data-src="([^"]+)"', card_html)
            if poster_m:
                poster = poster_m.group(1)
            if not poster:
                poster_m = re.search(r'<img[^>]+src="([^"]+)"', card_html)
                if poster_m:
                    poster = poster_m.group(1)

            year = extract_year_from_title(alt_m.group(1) if alt_m else '')

            rating = ''
            rating_m = re.search(r'class="[^"]*imdbRating[^"]*"[^>]*>\s*(\d+\.?\d*)', card_html, re.DOTALL)
            if rating_m:
                rating = rating_m.group(1)

            genre = ''
            li_list = re.findall(r'<li>(.*?)</li>', card_html)
            if li_list:
                genre = li_list[0].strip() if len(li_list) > 0 else ''

            items.append({
                'url': url,
                'title': title,
                'poster': poster,
                'year': year,
                'rating': rating,
                'genre': genre,
            })

            idx = next_pos if next_pos != -1 else pos + len(card_html)
        except:
            idx = pos + 1
            continue
    return items

def run_listing(start, end, workers, resume=False):
    path = os.path.join(DATA_DIR, 'topcinema_listing.json')
    all_items = load_json(path) if resume else []
    existing = {it['url'] for it in all_items}
    pages = list(range(start, end + 1))
    with ThreadPoolExecutor(max_workers=min(workers, 8)) as ex:
        futs = {ex.submit(listing_page, p): p for p in pages}
        for f in as_completed(futs):
            p_ = futs[f]
            try:
                new = f.result()
                cnt = 0
                for it in new:
                    if it['url'] not in existing:
                        all_items.append(it)
                        existing.add(it['url'])
                        cnt += 1
                p(f'  ✅ صفحة {p_}: +{cnt} ({len(all_items)})')
            except Exception as e:
                p(f'  ❌ صفحة {p_}: {e}')
    save_json(path, all_items)
    p(f'📁 القائمة: {len(all_items)} فيلم')
    return all_items

def extract_movie_details(url):
    """استخراج تفاصيل الفلم من صفحة الفلم"""
    html = fetch_text(url)
    det = {}
    det['url'] = url

    # Title from h1 with post-title class (movie title)
    h1 = re.search(r'<h1[^>]*class="[^"]*post-title[^"]*"[^>]*>(.*?)</h1>', html, re.DOTALL)
    if h1:
        full_title = re.sub(r'<[^>]+>', '', h1.group(1)).strip()
        det['title'] = extract_en_title(full_title)
        if not det.get('year'):
            det['year'] = extract_year_from_title(full_title)
    else:
        # Fallback: og:title
        ogt = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html)
        if ogt:
            det['title'] = extract_en_title(ogt.group(1))

    # Poster - from the detail page
    poster = re.search(r'<div class="image">\s*<img[^>]+src="([^"]+)"', html, re.DOTALL)
    if poster:
        det['poster'] = poster.group(1)
    if not det.get('poster'):
        pm = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
        if pm:
            det['poster'] = pm.group(1)
    if not det.get('poster'):
        pm2 = re.search(r'<img[^>]+class="[^"]*poster[^"]*"[^>]+src="([^"]+)"', html)
        if pm2:
            det['poster'] = pm2.group(1)

    # Description
    desc = re.search(r'<div class="story">\s*<p>(.*?)</p>', html, re.DOTALL)
    if desc:
        det['description'] = re.sub(r'<[^>]+>', '', desc.group(1)).strip()
    if not det.get('description'):
        dm = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html)
        if dm:
            det['description'] = dm.group(1)

    # Rating from IMDB
    rating = re.search(r'(\d+\.?\d*)\s*/\s*10\s*stars?\s*from', html, re.DOTALL)
    if rating:
        det['rating'] = rating.group(1)
    if not det.get('rating'):
        rating2 = re.search(r'class="[^"]*imdbRate[^"]*"[^>]*>.*?(\d+\.?\d*)', html, re.DOTALL)
        if rating2:
            det['rating'] = rating2.group(1)

    # Details from RightTaxContent
    details = {}
    dt_section = re.search(r'<ul\s+class="RightTaxContent">(.*?)</ul>', html, re.DOTALL)
    if dt_section:
        lis = re.findall(r'<li[^>]*>(.*?)</li>', dt_section.group(1), re.DOTALL)
        for li in lis:
            span_m = re.search(r'<span>(.*?)</span>', li)
            if not span_m:
                continue
            label = span_m.group(1).strip()
            a_m = re.findall(r'<a[^>]*>([^<]+)</a>', li)
            value = '، '.join(a_m) if a_m else ''
            details[label] = value

    det['category'] = details.get('قسم الفيلم :', '')
    det['genre'] = details.get('نوع الفيلم :', '')
    det['quality'] = details.get('جودة الفيلم :', '')
    det['year'] = det.get('year') or details.get('موعد الصدور :', '')
    det['language'] = details.get('لغة الفيلم :', '')
    det['country'] = details.get('دولة الفيلم :', '')
    cast_str = details.get('بطولة  :', '') or details.get('بطولة :', '')
    if cast_str:
        det['cast'] = [c.strip() for c in cast_str.split('،') if c.strip()]

    # Watch servers - try watch page for data-id, then AJAX for iframe URLs
    watch_url = url.rstrip('/') + '/watch/'
    servers = []
    try:
        watch_html = fetch_text(watch_url)
        # Get post ID from data-id on server items
        post_id = ''
        server_items = re.findall(
            r'<li[^>]*data-id="(\d+)"[^>]*data-server="(\d+)"[^>]*class="[^"]*server--item[^"]*"[^>]*>.*?<span>(.*?)</span>',
            watch_html, re.DOTALL
        )
        if not server_items:
            # Fallback: simpler pattern
            server_items = re.findall(
                r'<li[^>]*data-id="(\d+)"[^>]*data-server="(\d+)"[^>]*>.*?<span>(.*?)</span>',
                watch_html, re.DOTALL
            )

        if server_items:
            post_id = server_items[0][0]
            # Call AJAX for each server
            ajax_url = AJAX_URL + 'Single/Server.php'
            for data_id, data_server, name_text in server_items:
                name = name_text.strip()
                if name == 'Cinema':
                    continue
                try:
                    ajax_resp = get_session().post(ajax_url, data={'id': post_id, 'i': data_server},
                                                      headers={'X-Requested-With': 'XMLHttpRequest'}, timeout=15)
                    ajax_resp.encoding = 'utf-8'
                    iframe_m = re.search(r'<iframe[^>]+src="([^"]+)"', ajax_resp.text)
                    iframe_url = iframe_m.group(1) if iframe_m else ''
                    servers.append({
                        'name': name,
                        'url': iframe_url,
                        'isDefault': len(servers) == 0,
                    })
                except:
                    servers.append({
                        'name': name,
                        'url': '',
                        'isDefault': len(servers) == 0,
                    })
    except:
        # Fallback: look for iframe in main page
        iframe_m = re.search(r'<iframe[^>]+src="([^"]+)"', html)
        if iframe_m:
            servers = [{'name': 'Embed Player', 'url': iframe_m.group(1), 'isDefault': True}]

    det['servers'] = servers

    # Download links
    download_servers = []
    # Download page link
    dl_page_m = re.search(r'<a\s+class="[^"]*download[^"]*"\s+href="([^"]+)"', html)
    if dl_page_m:
        det['download_page'] = dl_page_m.group(1)
        # Try to scrape download page
        try:
            dl_html = fetch_text(det['download_page'])
            download_servers = extract_download_links(dl_html)
        except:
            pass

    # Also try to find download links directly on the page (DownloadBox)
    dl_box = re.search(r'<div\s+class="DownloadBox">(.*?)</div>\s*</div>', html, re.DOTALL)
    if dl_box and not download_servers:
        download_servers = extract_download_links_from_box(dl_box.group(1))

    # If still no download links, try to find any download URLs in the page
    if not download_servers:
        dl_links = re.findall(r'<a[^>]*class="[^"]*downloadsLink[^"]*"[^>]*href="([^"]+)"[^>]*>.*?<span>(.*?)</span>', html, re.DOTALL)
        for dl_url, dl_name in dl_links:
            download_servers.append({
                'name': dl_name.strip(),
                'url': dl_url,
            })

    det['downloadServers'] = download_servers

    return det

def extract_download_links(html):
    """استخراج روابط التحميل من صفحة التحميل"""
    servers = []
    # Pro servers (multi-quality)
    pro_servers = re.findall(
        r'<a\s+target="[^"]*"[^>]*rel="[^"]*"[^>]*href="([^"]+)"[^>]*class="[^"]*downloadsLink[^"]*"[^>]*>.*?<span>(.*?)</span>.*?<p>(.*?)</p>',
        html, re.DOTALL
    )
    for dl_url, dl_name, dl_quality in pro_servers:
        servers.append({
            'name': f'{dl_name.strip()} ({dl_quality.strip()})',
            'url': dl_url,
        })

    # DownloadBlock items
    dl_blocks = re.findall(
        r'<div\s+class="DownloadBlock">(.*?)</div>\s*</div>',
        html, re.DOTALL
    )
    for block in dl_blocks:
        quality_m = re.search(r'<span>(\d+p[^<]*)</span>', block)
        quality = quality_m.group(1) if quality_m else ''
        links = re.findall(
            r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*downloadsLink[^"]*"[^>]*>.*?<span>(.*?)</span>.*?<p>(.*?)</p>',
            block, re.DOTALL
        )
        for dl_url, dl_name, dl_qual in links:
            servers.append({
                'name': f'{dl_name.strip()} ({quality or dl_qual.strip()})',
                'url': dl_url,
            })

    return servers

def extract_download_links_from_box(html):
    """استخراج روابط التحميل من DownloadBox على صفحة الفلم"""
    servers = []
    links = re.findall(
        r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*downloadsLink[^"]*"[^>]*>.*?<span>(.*?)</span>',
        html, re.DOTALL
    )
    for dl_url, dl_name in links:
        servers.append({
            'name': dl_name.strip(),
            'url': dl_url,
        })
    return servers

def run_detail(movie_list, workers, resume=False):
    total = len(movie_list)
    path = os.path.join(DATA_DIR, 'topcinema_detail.json')
    if resume and os.path.exists(path):
        existing = load_json(path)
        exist_urls = {m.get('url', ''): m for m in existing if m.get('url')}
        p(f'📂 تحميل {len(existing)} فيلم من النتائج السابقة')
    else:
        existing = []
        exist_urls = {}
    todo = [m for m in movie_list if m['url'] not in exist_urls]
    done = 0
    results = existing[:]

    def process(m):
        time.sleep(0.3)
        det = extract_movie_details(m['url'])
        det.setdefault('title', m.get('title', ''))
        if not det.get('poster') and m.get('poster'):
            det['poster'] = m['poster']
        if not det.get('year') and m.get('year'):
            det['year'] = m['year']
        if not det.get('rating') and m.get('rating'):
            det['rating'] = m['rating']
        return det

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(process, m): m for m in todo}
        for f in as_completed(futs):
            done += 1
            m = futs[f]
            try:
                det = f.result()
                results.append(det)
                p(f'  ✅ [{done}/{len(todo)}] {det.get("title", "")[:50]}')
            except Exception as e:
                p(f'  ❌ [{done}/{len(todo)}] {m.get("title", "")[:50]}: {e}')
                results.append(m)
            if done % 25 == 0:
                save_json(path, results)
                p(f'  💾 حفظ: {done}/{len(todo)}')
    save_json(path, results)
    p(f'📁 التفاصيل: {len(results)} فيلم')
    return results

def to_site_format(movie_list):
    out = []
    for m in movie_list:
        title = m.get('title', '')
        if not title:
            continue
        genres = []
        if m.get('genre'):
            genres = [g.strip() for g in m['genre'].split('،') if g.strip()]
        cast = m.get('cast', [])
        if isinstance(cast, str):
            cast = [c.strip() for c in cast.split('،') if c.strip()]
        item = {
            'title': title,
            'year': m.get('year', ''),
            'rating': m.get('rating', ''),
            'quality': m.get('quality', ''),
            'type': 'أجنبي',
            'contentType': 'movie',
            'description': m.get('description', ''),
            'cast': cast if cast else [' '],
            'poster': m.get('poster', ''),
            'categories': genres,
            'servers': m.get('servers', []),
            'downloadServers': m.get('downloadServers', []),
            'language': m.get('language', ''),
            'country': m.get('country', ''),
            'isComplete': False,
        }
        out.append(item)
    out.sort(key=lambda x: x['title'].strip())
    return out

def save_site_format(data_list, output_path=None):
    if output_path is None:
        output_path = OUTPUT_FILE
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f'// أفلام أجنبية من TopCinema — {len(data_list)} فيلم\n')
        f.write(f'// تم التوليد: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write('const cd_foreign = ')
        json.dump(data_list, f, ensure_ascii=False, indent=2)
    p(f'📁 تم الحفظ: {output_path} ({len(data_list)} فيلم)')
    return output_path

def main():
    parser = argparse.ArgumentParser(description='سكربت سحب أفلام أجنبية من TopCinema')
    parser.add_argument('--start', type=int, default=1, help='صفحة البداية (افتراضي: 1)')
    parser.add_argument('--end', type=int, default=5, help='صفحة النهاية (افتراضي: 5)')
    parser.add_argument('--workers', type=int, default=4, help='عدد العمال (افتراضي: 4)')
    parser.add_argument('--phase', choices=['all', 'listing', 'detail'], default='all', help='المرحلة')
    parser.add_argument('--resume', action='store_true', help='استئناف من النتائج السابقة')
    parser.add_argument('--convert', action='store_true', help='تحويل نتائج JSON إلى صيغة الموقع فقط')
    parser.add_argument('--output', type=str, default='', help='ملف الإخراج')
    args = parser.parse_args()

    p('=' * 55)
    p(f'📺 سحب أفلام أجنبية من TopCinema - صفحات {args.start}-{args.end}')
    p(f'   عمال: {args.workers} | مرحلة: {args.phase}')
    p('=' * 55)

    if args.convert:
        path = os.path.join(DATA_DIR, 'topcinema_detail.json')
        if not os.path.exists(path):
            path2 = os.path.join(DATA_DIR, 'topcinema_listing.json')
            if not os.path.exists(path2):
                p(f'❌ الملف غير موجود: topcinema_detail.json')
                return
            # Convert listing to detail format (minimal)
            data = load_json(path2)
            converted = to_site_format(data)
        else:
            data = load_json(path)
            p(f'📂 تحميل {len(data)} فيلم من {path}')
            converted = to_site_format(data)
        output = args.output if args.output else OUTPUT_FILE
        save_site_format(converted, output)
        return

    if args.phase in ('all', 'listing'):
        p('\n=== المرحلة 1: القائمة ===')
        items = run_listing(args.start, args.end, args.workers, resume=args.resume)
        save_json(os.path.join(DATA_DIR, 'topcinema_full.json'), items)
    else:
        for fname in ['topcinema_full.json', 'topcinema_detail.json', 'topcinema_listing.json']:
            fp = os.path.join(DATA_DIR, fname)
            if os.path.exists(fp):
                items = load_json(fp)
                p(f'📂 تحميل {fname}: {len(items)} عنصر')
                break
        else:
            p('❌ لا توجد بيانات. شغّل --phase listing أولاً')
            return

    if args.phase in ('all', 'detail'):
        p('\n=== المرحلة 2: تفاصيل الأفلام ===')
        items = run_detail(items, args.workers, resume=args.resume)

    final_path = os.path.join(DATA_DIR, 'topcinema_full.json')
    save_json(final_path, items)
    total_srv = sum(len(m.get('servers', [])) for m in items)
    total_dl = sum(len(m.get('downloadServers', [])) for m in items)
    p(f'\n✅ تم: {len(items)} فيلم, {total_srv} سيرفر, {total_dl} رابط تحميل')
    p(f'📁 {final_path}')

    converted = to_site_format(items)
    output = args.output if args.output else OUTPUT_FILE
    save_site_format(converted, output)

if __name__ == '__main__':
    main()
