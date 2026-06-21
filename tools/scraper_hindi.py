import requests
import json
import re
import time
import argparse
import sys
import io
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7'
})

BASE_URL = "https://www.tuktukcinma.com"
DEFAULT_CATEGORY = f"{BASE_URL}/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D9%87%D9%86%D8%AF%D9%89/"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_JS_PATH = os.path.join(SCRIPT_DIR, 'data.js')

def normalize(t):
    t = t.strip()
    t = re.sub(r'\s+', '', t)
    for y in ['2024','2023','2025','2022','2021','2020','2019','2018','2017','2016','2015']:
        t = t.replace(y, '')
    t = re.sub(r'^فيلم', '', t)
    t = re.sub(r'^مسلسل', '', t)
    t = re.sub(r'^فلم', '', t)
    t = t.strip()
    t = re.sub(r'[\u064B-\u0652]', '', t)
    return t.lower()

def load_data_js():
    with open(DATA_JS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    arr_start = content.index('[')
    arr_end = content.rindex(']') + 1
    data = json.loads(content[arr_start:arr_end])
    return data, content[:arr_start], content[arr_end:]

def save_data_js(data, prefix, suffix):
    json_str = json.dumps(data, ensure_ascii=False)
    with open(DATA_JS_PATH, 'w', encoding='utf-8') as f:
        f.write(prefix + json_str + suffix)
    size = os.path.getsize(DATA_JS_PATH)
    print(f'  💾 data.js: {len(data)} items, {size/1024:.0f} KB')

def is_duplicate(new_title, existing_data):
    new_norm = normalize(new_title)
    if not new_norm:
        return None
    for item in existing_data:
        existing_norm = normalize(item.get('title', ''))
        if new_norm == existing_norm:
            return item
        if new_norm in existing_norm or existing_norm in new_norm:
            longer = max(len(new_norm), len(existing_norm))
            shorter = min(len(new_norm), len(existing_norm))
            if shorter > 0 and longer / shorter < 1.3:
                return item
    return None

def clean_title(title):
    if not title:
        return ''
    cleaned = re.sub(r'فيلم\s*', '', title, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*مترجم\s*اون\s*لاين\s*$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*مترجم\s*أون\s*لاين\s*$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*مترجم\s*اون-لاين\s*$', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

def extract_text(element, default=''):
    return element.get_text(strip=True) if element else default

def extract_attr(element, attr, default=''):
    return element.get(attr, default) if element else default

def get_page_soup(url):
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f'  ❌ خطأ في جلب الصفحة: {e}')
        return None

def extract_movie_links(category_url, page):
    url = f'{category_url}?page={page}'
    soup = get_page_soup(url)
    if not soup:
        return []
    movies = []
    items = soup.select('div.Block--Item a')
    for item in items:
        href = item.get('href')
        title = item.get('title') or extract_text(item.select_one('h2.title'))
        if href and title:
            full_url = urljoin(BASE_URL, href) if not href.startswith('http') else href
            img = item.select_one('img')
            src = extract_attr(img, 'src')
            data_src = extract_attr(img, 'data-src')
            poster = data_src if (not src or 'no.png' in src) else src
            movies.append({
                'url': full_url,
                'title': clean_title(title),
                'poster': poster
            })
    return movies

def extract_movie_details(movie_url):
    soup = get_page_soup(movie_url)
    if not soup:
        return None

    movie_data = {}

    title = soup.select_one('h1.entry-title') or soup.select_one('h1')
    if title:
        movie_data['title'] = clean_title(extract_text(title))
    else:
        meta_title = soup.select_one('meta[property="og:title"]')
        movie_data['title'] = clean_title(extract_attr(meta_title, 'content')) if meta_title else ''

    og_image = soup.select_one('meta[property="og:image"]')
    poster = (soup.select_one('div.Poster--Block img') or
              soup.select_one('.Poster--Block img') or
              soup.select_one('div[class*="Poster"] img'))
    if poster:
        p_src = extract_attr(poster, 'src')
        p_data = extract_attr(poster, 'data-src')
        poster_url = p_data if (not p_src or 'no.png' in p_src) else p_src
        movie_data['poster'] = urljoin(BASE_URL, poster_url) if poster_url and not poster_url.startswith('http') else poster_url
    elif og_image:
        movie_data['poster'] = extract_attr(og_image, 'content')

    # Details from RightTaxContent
    info_dict = {}
    for li in soup.select('ul.RightTaxContent li'):
        span = li.select_one('span')
        if not span:
            continue
        key = span.get_text(strip=True).rstrip(':').strip()
        values = []
        for child in li.find_all(['a', 'strong']):
            values.append(child.get_text(strip=True))
        if values:
            info_dict[key] = ' '.join(values)

    movie_data['year'] = info_dict.get('موعد الصدور', '')
    movie_data['rating'] = info_dict.get('تقييم الفيلم', '')
    movie_data['duration'] = info_dict.get('توقيت الفيلم', '')
    movie_data['quality'] = info_dict.get('جودة الفيلم', '')

    if not movie_data['year']:
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', movie_data.get('title', ''))
        if year_match:
            movie_data['year'] = year_match.group(1)

    # Story
    story = soup.select_one('div.story') or soup.select_one('.story')
    movie_data['description'] = extract_text(story) if story else ''

    # Categories
    categories = []
    for a in soup.select('div.catssection a'):
        cat = a.get_text(strip=True)
        if cat and cat not in categories:
            categories.append(cat)
    movie_data['categories'] = categories

    # Cast
    cast_raw = info_dict.get('بطولة', '')
    cast = [a.strip() for a in re.split(r'[-–—,/\n]+', cast_raw) if a.strip()] if cast_raw else []
    movie_data['cast'] = cast

    # Servers from data-link
    servers = []
    for item in soup.select('li.server--item'):
        data_link = item.get('data-link')
        if data_link:
            server_name = extract_text(item.select_one('span')) or 'Server'
            servers.append({
                'name': server_name.strip(),
                'url': f'{BASE_URL}/watch?token={data_link}',
                'isDefault': 'active' in (item.get('class') or [])
            })
    if not servers:
        watch_link = soup.select_one('a.watchAndDownlaod')
        servers.append({
            'name': 'TukTuk',
            'url': extract_attr(watch_link, 'href') or movie_url,
            'isDefault': True
        })
    movie_data['servers'] = servers

    # Download servers
    download_servers = []
    for link in soup.select('a[data-real-url]'):
        real_url = extract_attr(link, 'data-real-url')
        server_name = extract_text(link.select_one('span')) or 'Download'
        if real_url:
            try:
                import base64
                decoded = base64.b64decode(real_url).decode('utf-8')
                download_servers.append({'name': server_name.strip(), 'url': decoded})
            except:
                download_servers.append({'name': server_name.strip(), 'url': real_url})
    if not download_servers:
        download_servers.append({'name': 'الصفحة الرسمية', 'url': movie_url})
    movie_data['downloadServers'] = download_servers

    # Trail
    trailer = soup.select_one('a[href*="youtube.com"]') or soup.select_one('iframe[src*="youtube"]')
    if trailer:
        trailer_url = extract_attr(trailer, 'href') or extract_attr(trailer, 'src')
        if trailer_url and 'watch?v=' in trailer_url:
            video_id = trailer_url.split('watch?v=')[-1].split('&')[0]
            movie_data['trial'] = f'https://www.youtube.com/embed/{video_id}'
    movie_data.setdefault('trial', '')

    movie_data['type'] = 'هندي'
    movie_data['contentType'] = 'movie'

    return movie_data

def scrape_movie_range(category_url, page, start_movie, end_movie, delay=2):
    movies = extract_movie_links(category_url, page)
    if not movies:
        print('❌ لم يتم العثور على أفلام في هذه الصفحة')
        return []
    if start_movie > len(movies) or end_movie > len(movies):
        print(f'❌ الصفحة تحتوي على {len(movies)} فيلم فقط')
        return []

    existing_data, prefix, suffix = load_data_js()
    added = 0
    skipped = 0
    start_time = datetime.now()

    for idx in range(start_movie, end_movie + 1):
        movie = movies[idx - 1]
        print(f'\n  [{idx - start_movie + 1}/{end_movie - start_movie + 1}] {movie["title"]}')

        details = extract_movie_details(movie['url'])
        if not details:
            print('  ⚠️ فشل الاستخراج')
            if idx < end_movie:
                time.sleep(delay)
            continue

        # Use poster from listing if detail has no.png
        if not details.get('poster') or 'no.png' in details.get('poster', ''):
            if movie.get('poster') and 'no.png' not in movie.get('poster', ''):
                details['poster'] = movie['poster']

        dup = is_duplicate(details['title'], existing_data)
        if dup:
            print(f'  ⏭️ موجود مسبقاً: "{dup["title"]}"')
            skipped += 1
        else:
            existing_data.append(details)
            added += 1
            print(f'  ✅ تمت الإضافة')

        if idx < end_movie:
            time.sleep(delay)

    duration_s = (datetime.now() - start_time).total_seconds()

    if added > 0:
        save_data_js(existing_data, prefix, suffix)
    print(f'\n  📊 الموجود: {skipped} | المضاف: {added} | الإجمالي: {len(existing_data)}')
    print(f'  ⏱️ {duration_s:.1f} ثانية')
    return True

def main():
    parser = argparse.ArgumentParser(description='🎬 سكربت tuktukcinma (أفلام هندي) → الموقع')
    parser.add_argument('-p', '--page', type=int, default=1, help='رقم الصفحة')
    parser.add_argument('-s', '--start', type=int, default=1, help='رقم فيلم البداية')
    parser.add_argument('-e', '--end', type=int, default=10, help='رقم فيلم النهاية')
    parser.add_argument('-u', '--url', type=str, default=DEFAULT_CATEGORY, help='رابط التصنيف')
    parser.add_argument('-d', '--delay', type=int, default=2, help='التأخير بين الطلبات (ثانية)')
    parser.add_argument('--insert', action='store_true', help='💡 إدراج مباشر في data.js')

    args = parser.parse_args()

    if not args.insert:
        print('⚠️ استخدم --insert للإدراج في data.js')
        return

    print(f'\n{"="*60}')
    print(f'  🎬 سكربت tuktukcinma → الموقع')
    print(f'  📂 {SCRIPT_DIR}')
    print(f'{"="*60}\n')

    scrape_movie_range(args.url, args.page, args.start, args.end, args.delay)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\n⚠️ تم الإيقاف')
        sys.exit(0)
    except Exception as e:
        print(f'\n❌ {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
