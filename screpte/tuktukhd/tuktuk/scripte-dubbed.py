#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكربت استخراج بيانات الأفلام المدبلجة من موقع tuktukhd.com
ودمجها تلقائياً في ملف data.js الخاص بالموقع
"""

import requests
import json
import re
import time
import argparse
import sys
import os
import io
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from pathlib import Path
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://tuktukhd.com/'
})

BASE_URL = "https://tuktukhd.com"
DEFAULT_CATEGORY = "https://tuktukhd.com/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D9%85%D8%AF%D8%A8%D9%84%D8%AC%D8%A9/"

SCRIPT_DIR = os.path.dirname(os.path.dirname(__file__))  # الر archid-site
DATA_JS_PATH = os.path.join(SCRIPT_DIR, 'data.js')
ELCINEMA_CACHE_PATH = os.path.join(SCRIPT_DIR, 'elcinema_cache.json')

# ── Normalization (same as elcinema_search.py) ──
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

# ── Data.js I/O ──
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

# ── Elcinema poster lookup ──
def load_elcinema_cache():
    try:
        with open(ELCINEMA_CACHE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def search_elcinema(title, cache):
    best = None
    best_score = 0
    norm = normalize(title)
    if not norm:
        return None
    for cached_title, data in cache.items():
        cached_norm = normalize(cached_title)
        if norm == cached_norm:
            return data.get('poster', '')
        common = sum(1 for c in norm if c in cached_norm)
        if common > 0:
            sim = common / max(len(norm), len(cached_norm))
            if sim > 0.8 and sim > best_score:
                best_score = sim
                best = data.get('poster', '')
    return best

# ── Scraping functions ──
def ensure_directory(filepath):
    path = Path(filepath).resolve()
    directory = path.parent
    if not directory.exists() and str(directory) not in ['.', '']:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f'⚠️ تحذير: {directory}: {e}')
    return path

def clean_title(title):
    if not title:
        return ''
    cleaned = re.sub(r'فيلم\s*', '', title, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*مترجم\s*اون\s*لاين\s*$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*مترجم\s*أون\s*لاين\s*$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*مترجم\s*اون-لاين\s*$', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

def decode_server_token(token):
    try:
        part = token.split('0REL0Y&')[0]
        reversed_part = part[::-1]
        import base64
        return base64.b64decode(reversed_part).decode('utf-8')
    except:
        return None

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
    print('    🌐 جلب الصفحة...', end=' ', flush=True)
    soup = get_page_soup(movie_url)
    if not soup:
        print('❌')
        return None
    print('✅')

    movie_data = {}

    title = soup.select_one('h1.entry-title') or soup.select_one('h1')
    if title:
        movie_data['title'] = clean_title(extract_text(title))
    else:
        meta_title = soup.select_one('meta[property="og:title"]')
        movie_data['title'] = clean_title(extract_attr(meta_title, 'content')) if meta_title else 'عنوان غير معروف'
    print(f'    🏷️ العنوان: {movie_data["title"]}')

    print('    🖼️ البوستر...', end=' ', flush=True)
    og_image = soup.select_one('meta[property="og:image"]')
    poster = (soup.select_one('div.Poster--Block img') or
              soup.select_one('.Poster--Block img') or
              soup.select_one('div[class*="Poster"] img') or
              soup.select_one('.poster img'))
    if poster:
        p_src = extract_attr(poster, 'src')
        p_data = extract_attr(poster, 'data-src')
        poster_url = p_data if (not p_src or 'no.png' in p_src) else p_src
        movie_data['poster'] = urljoin(BASE_URL, poster_url) if poster_url and not poster_url.startswith('http') else poster_url
    elif og_image:
        movie_data['poster'] = extract_attr(og_image, 'content')
    print('✅' if movie_data.get('poster') else '⚠️')

    year_elem = soup.select_one('li:has(i.fa-calendar) a[href*="release-year"]')
    movie_data['year'] = extract_text(year_elem).strip() if year_elem else ''
    print(f'    📅 السنة: {movie_data["year"] or "—"}')

    rating = (soup.select_one('li:has(i.fa-star) strong') or
              soup.select_one('div.rating-box strong') or
              soup.select_one('.imdb-rating strong') or
              soup.select_one('[class*="rating"] strong') or
              soup.select_one('div[class*="imdb"] strong'))
    movie_data['rating'] = extract_text(rating).strip() if rating else ''
    print(f'    ⭐ التقييم: {movie_data["rating"] or "—"}')

    duration = soup.select_one('li:has(i.fa-clock) strong') or soup.select_one('li:has(.fal.fa-clock) strong')
    if duration:
        dur_text = extract_text(duration).strip()
        minutes = re.search(r'(\d+)', dur_text)
        movie_data['duration'] = f'{minutes.group(1)} دقيقة' if minutes else dur_text
    else:
        movie_data['duration'] = ''
    print(f'    ⏱️ المدة: {movie_data["duration"] or "—"}')

    quality = soup.select_one('li:has(i.fa-play) a[href*="quality"]')
    movie_data['quality'] = extract_text(quality).strip() if quality else ''
    print(f'    📺 الجودة: {movie_data["quality"] or "—"}')

    movie_data['type'] = 'مسلسل' if '/series/' in movie_url.lower() else 'فيلم'
    print(f'    🎞️ النوع: {movie_data["type"]}')

    story = soup.select_one('div.story') or soup.select_one('div.description')
    if story:
        movie_data['description'] = extract_text(story).strip()
    else:
        meta_desc = soup.select_one('meta[name="description"]') or soup.select_one('meta[property="og:description"]')
        movie_data['description'] = extract_attr(meta_desc, 'content').strip() if meta_desc else ''
    desc_preview = movie_data['description'][:60] + '...' if len(movie_data['description']) > 60 else movie_data['description']
    print(f'    📝 القصة: {desc_preview or "—"}')

    cast = []
    cast_section = soup.select_one('li:has(span:-soup-contains("بطولة"))')
    if cast_section:
        for link in cast_section.select('a[href*="/actor/"]'):
            name = extract_text(link).strip()
            if name and name not in cast:
                cast.append(name)
    movie_data['cast'] = cast
    print(f'    👥 التمثيل: {len(cast)} ممثل')

    categories = []
    genre_section = soup.select_one('li:has(span:-soup-contains("الانواع"))') or soup.select_one('ul.Genres')
    if genre_section:
        for item in genre_section.select('a[href*="/genre/"]') or genre_section.select('li'):
            cat = extract_text(item).strip()
            if cat and cat not in categories:
                categories.append(cat)
    movie_data['categories'] = categories
    print(f'    🏷️ التصنيفات: {", ".join(categories) if categories else "—"}')

    servers = []
    for item in soup.select('li.server--item'):
        server_name = extract_text(item.select_one('span')).strip() or 'Server'
        data_link = extract_attr(item, 'data-link')
        if data_link:
            decoded_url = decode_server_token(data_link)
            servers.append({
                'name': server_name,
                'url': decoded_url or f'{BASE_URL}/watch?token={data_link}',
                'isDefault': 'active' in (item.get('class') or [])
            })
    if not servers:
        servers.append({'name': 'TukTuk Vip', 'url': movie_url, 'isDefault': True})
    movie_data['servers'] = servers
    print(f'    📡 السيرفرات: {len(servers)}')

    download_servers = []
    for link in soup.select('a[data-real-url]'):
        real_url = extract_attr(link, 'data-real-url')
        server_name = extract_text(link.select_one('span')).strip() or 'Download'
        if real_url:
            parsed = urlparse(real_url)
            qs = parse_qs(parsed.query)
            if 'u' in qs:
                import base64
                try:
                    decoded = base64.b64decode(qs['u'][0]).decode('utf-8')
                    download_servers.append({'name': server_name, 'url': decoded})
                except:
                    download_servers.append({'name': server_name, 'url': real_url})
            else:
                download_servers.append({'name': server_name, 'url': real_url})
    if not download_servers:
        download_servers.append({'name': 'الصفحة الرسمية', 'url': movie_url})
    movie_data['downloadServers'] = download_servers
    print(f'    ⬇️ روابط التحميل: {len(download_servers)}')

    trailer = soup.select_one('a[href*="youtube.com"]') or soup.select_one('iframe[src*="youtube"]')
    if trailer:
        trailer_url = extract_attr(trailer, 'href') or extract_attr(trailer, 'src')
        if trailer_url and 'watch?v=' in trailer_url:
            video_id = trailer_url.split('watch?v=')[-1].split('&')[0]
            movie_data['trial'] = f'https://www.youtube.com/embed/{video_id}'
    else:
        movie_data['trial'] = ''
    print(f'    🎬 إعلان: {"✅" if movie_data.get("trial") else "—"}')

    movie_data['contentType'] = 'movie' if movie_data['type'] == 'فيلم' else 'series'

    return movie_data

def format_movie_data(raw_data):
    return {
        'title': raw_data.get('title', ''),
        'year': raw_data.get('year', ''),
        'rating': raw_data.get('rating', ''),
        'duration': raw_data.get('duration', ''),
        'quality': raw_data.get('quality', ''),
        'type': raw_data.get('type', ''),
        'description': raw_data.get('description', ''),
        'cast': raw_data.get('cast', []),
        'categories': raw_data.get('categories', []),
        'poster': raw_data.get('poster', ''),
        'servers': raw_data.get('servers', []),
        'downloadServers': raw_data.get('downloadServers', []),
        'trial': raw_data.get('trial', ''),
        'contentType': raw_data.get('contentType', 'movie')
    }

def save_to_json(data, filename):
    if not filename.endswith('.json'):
        filename += '.json'
    full_path = ensure_directory(filename)
    abs_path = os.path.abspath(full_path)
    data_list = data if isinstance(data, list) else [data]
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)
    file_size = os.path.getsize(full_path)
    print(f'\n  ✅ حفظ {len(data_list)} فيلم → {abs_path} ({file_size/1024:.1f} KB)')
    return True

def list_movies_on_page(category_url, page):
    movies = extract_movie_links(category_url, page)
    if not movies:
        print('⚠️ لم يتم العثور على أفلام في هذه الصفحة')
        return None
    print(f'\n📋 الصفحة {page} — {len(movies)} فيلم:')
    print('=' * 70)
    for idx, movie in enumerate(movies, 1):
        print(f'  {idx:2d}. {movie["title"]}')
    print('=' * 70)
    return movies

def scrape_movie_range(category_url, page, start_movie, end_movie, output_file, delay=2, insert_mode=False):
    movies = extract_movie_links(category_url, page)
    if not movies:
        print('❌ لم يتم العثور على أفلام في هذه الصفحة')
        return None
    if start_movie > len(movies) or end_movie > len(movies):
        print(f'❌ الصفحة تحتوي على {len(movies)} فيلم فقط')
        return None

    if insert_mode:
        existing_data, prefix, suffix = load_data_js()
        elcache = load_elcinema_cache()
        added = 0
        skipped = 0
    else:
        all_movies = []

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

        formatted = format_movie_data(details)

        listing_poster = movie.get('poster', '')
        if listing_poster and 'no.png' not in listing_poster:
            formatted['poster'] = listing_poster
        elif not formatted.get('poster') or 'no.png' in formatted.get('poster', ''):
            formatted['poster'] = listing_poster

        if insert_mode:
            dup = is_duplicate(formatted['title'], existing_data)
            if dup:
                print(f'  ⏭️ موجود مسبقاً: "{dup["title"]}"')
                skipped += 1
            else:
                # Try to get elcinema poster
                el_poster = search_elcinema(formatted['title'], elcache)
                if el_poster:
                    formatted['poster'] = el_poster
                    print(f'  🖼️ بوستر من elcinema')
                existing_data.append(formatted)
                added += 1
                print(f'  ✅ تمت الإضافة')
        else:
            all_movies.append(formatted)
            print(f'  ✅ تم الاستخراج')

        if idx < end_movie:
            time.sleep(delay)

    duration_s = (datetime.now() - start_time).total_seconds()

    if insert_mode:
        if added > 0:
            save_data_js(existing_data, prefix, suffix)
        print(f'\n  📊 الموجود: {skipped} | المضاف: {added} | الإجمالي: {len(existing_data)}')
    elif all_movies and output_file:
        save_to_json(all_movies, output_file)

    print(f'  ⏱️ {duration_s:.1f} ثانية')
    return True

def main():
    parser = argparse.ArgumentParser(
        description='🎬 سكربت استخراج ودمج أفلام مدبلجة من tuktukhd.com',
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-i', '--interactive', action='store_true', help='الوضع التفاعلي')
    parser.add_argument('-p', '--page', type=int, help='رقم الصفحة')
    parser.add_argument('-sm', '--start-movie', type=int, help='رقم فيلم البداية')
    parser.add_argument('-em', '--end-movie', type=int, help='رقم فيلم النهاية')
    parser.add_argument('-m', '--movie', type=int, help='رقم الفيلم (واحد)')
    parser.add_argument('-s', '--start', type=int, default=1, help='صفحة البداية')
    parser.add_argument('-e', '--end', type=int, default=1, help='صفحة النهاية')
    parser.add_argument('--all', action='store_true', help='كل الأفلام من start إلى end')
    parser.add_argument('-u', '--url', type=str, default=DEFAULT_CATEGORY, help='رابط التصنيف')
    parser.add_argument('-o', '--output', type=str, default='output.json', help='ملف إخراج JSON')
    parser.add_argument('-d', '--delay', type=int, default=2, help='التأخير بين الطلبات (ثانية)')
    parser.add_argument('--insert', action='store_true', help='💡 إدراج مباشر في data.js (بدون --output)')
    parser.add_argument('--list', action='store_true', help='عرض قائمة الأفلام فقط بدون استخراج')

    args = parser.parse_args()

    print(f'\n{"="*60}')
    print(f'  🎬 سكربت tuktuk (مدبلجة) → الموقع')
    print(f'  📂 {SCRIPT_DIR}')
    print(f'{"="*60}\n')

    # إذا لم يتم تحديد أي وضع، نفتح الوضع التفاعلي
    if not any([args.page, args.start_movie, args.end_movie, args.movie, args.all, args.list]):
        args.interactive = True

    # ── وضع عرض القائمة فقط ──
    if args.list:
        category_url = args.url
        for p in range(args.start, args.end + 1):
            list_movies_on_page(category_url, p)
        return

    # ── وضع تفاعلي ──
    if args.interactive:
        category_url = input(f'  🔗 رابط التصنيف (Enter للافتراضي):\n  {DEFAULT_CATEGORY}\n  > ').strip() or DEFAULT_CATEGORY
        while True:
            try:
                page = int(input('\n  📄 رقم الصفحة: ').strip())
                if page > 0: break
            except ValueError:
                pass
        movies = list_movies_on_page(category_url, page)
        if not movies:
            return
        print('\n  📌 خيارات:')
        print('    1. استخراج فيلم واحد')
        print('    2. نطاق أفلام')
        print('    3. عرض القائمة فقط')
        choice = input('\n  👉 (1-3): ').strip()
        if choice == '3':
            return

        single = choice == '1'
        if single:
            while True:
                try:
                    movie_num = int(input(f'\n  🎬 رقم الفيلم (1-{len(movies)}): ').strip())
                    if 1 <= movie_num <= len(movies): break
                except ValueError:
                    pass
            sm = em = movie_num
        else:
            while True:
                try:
                    sm = int(input(f'\n  🎬 من (1-{len(movies)}): ').strip())
                    if 1 <= sm <= len(movies): break
                except ValueError:
                    pass
            while True:
                try:
                    em = int(input(f'  🎬 إلى ({sm}-{len(movies)}): ').strip())
                    if sm <= em <= len(movies): break
                except ValueError:
                    pass

        insert_choice = input('\n  💾 وجهة الحفظ:\n    1. ملف JSON منفصل\n    2. إدراج مباشر في data.js\n  👉 (1-2): ').strip()
        insert_mode = insert_choice == '2'

        if not insert_mode:
            output = input(f'\n  💾 اسم ملف JSON (Enter → output.json): ').strip() or 'output.json'
        else:
            output = None

        confirm = input('\n  ✅ متابعة؟ (y/n): ').strip().lower()
        if confirm != 'y':
            print('  ❌ تم الإلغاء')
            return

        scrape_movie_range(category_url, page, sm, em, output, args.delay, insert_mode)
        return

    # ── وضع سطر الأوامر: استخراج ودمج مباشر ──
    insert_mode = args.insert

    if args.all:
        all_added = 0
        all_skipped = 0
        all_total = 0
        existing_data = None
        prefix = suffix = None

        all_movies = []
        if insert_mode:
            existing_data, prefix, suffix = load_data_js()
            elcache = load_elcinema_cache()

        print(f'\n  🔄 جاري عد الأفلام في الصفحات {args.start}-{args.end}...')
        total_movies = 0
        for p in range(args.start, args.end + 1):
            links = extract_movie_links(args.url, p)
            total_movies += len(links) if links else 0
            time.sleep(0.5)
        print(f'  📊 {total_movies} فيلم في {args.end-args.start+1} صفحات')

        processed = 0
        for p in range(args.start, args.end + 1):
            print(f'\n{"="*50}')
            print(f'  📄 الصفحة {p}')
            movies = extract_movie_links(args.url, p)
            if not movies:
                print('  ⚠️ لا توجد أفلام')
                continue
            print(f'  {len(movies)} فيلم')

            if insert_mode:
                for movie in movies:
                    processed += 1
                    dup = is_duplicate(movie['title'], existing_data)
                    if dup:
                        all_skipped += 1
                        print(f'\n  [{processed}/{total_movies}] ⏭️ {movie["title"]} (موجود)')
                        continue
                    print(f'\n  [{processed}/{total_movies}] ➕ {movie["title"]}')
                    details = extract_movie_details(movie['url'])
                    if not details:
                        time.sleep(args.delay)
                        continue
                    formatted = format_movie_data(details)
                    listing_poster = movie.get('poster', '')
                    if listing_poster and 'no.png' not in listing_poster:
                        formatted['poster'] = listing_poster
                    elif not formatted.get('poster') or 'no.png' in formatted.get('poster', ''):
                        formatted['poster'] = listing_poster
                    el_poster = search_elcinema(formatted['title'], elcache)
                    if el_poster:
                        formatted['poster'] = el_poster
                    existing_data.append(formatted)
                    all_added += 1
                    print(f'     ✅')
                    time.sleep(args.delay)
            else:
                for movie in movies:
                    processed += 1
                    print(f'\n  [{processed}/{total_movies}] ➕ {movie["title"]}')
                    details = extract_movie_details(movie['url'])
                    if not details:
                        time.sleep(args.delay)
                        continue
                    formatted = format_movie_data(details)
                    listing_poster = movie.get('poster', '')
                    if listing_poster and 'no.png' not in listing_poster:
                        formatted['poster'] = listing_poster
                    elif not formatted.get('poster') or 'no.png' in formatted.get('poster', ''):
                        formatted['poster'] = listing_poster
                    all_movies.append(formatted)
                    all_added += 1
                    print(f'     ✅')
                    time.sleep(args.delay)

            all_total += len(movies)

        if insert_mode and all_added > 0:
            save_data_js(existing_data, prefix, suffix)
            print(f'\n  {"="*50}')
            print(f'  📊 الإجمالي: {all_total} فيلم | {all_skipped} موجود | {all_added} مضاف | الكلي: {len(existing_data)}')
        elif insert_mode:
            print(f'\n  📊 {all_total} فيلم — الكل موجود مسبقاً')
        elif all_movies:
            output_path = args.output
            if not output_path.endswith('.json'):
                output_path += '.json'
            if os.path.exists(output_path):
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing_old = json.load(f)
                old_titles = {m.get('title', '') for m in existing_old}
                new_count = 0
                for m in all_movies:
                    if m.get('title') not in old_titles:
                        existing_old.append(m)
                        old_titles.add(m.get('title'))
                        new_count += 1
                all_movies = existing_old
                print(f'\n  📂 تم العثور على ملف قديم: {new_count} جديد + {len(existing_old)-new_count} قديم')
            save_to_json(all_movies, args.output)
        return

    # ── نطاق أفلام ──
    if args.start_movie and args.end_movie:
        if args.start_movie > args.end_movie:
            print('❌ start-movie > end-movie')
            return
        if insert_mode:
            scrape_movie_range(args.url, args.start, args.start_movie, args.end_movie, None, args.delay, True)
        else:
            scrape_movie_range(args.url, args.start, args.start_movie, args.end_movie, args.output, args.delay, False)
        return

    # ── فيلم واحد ──
    if args.page and args.movie:
        if insert_mode:
            scrape_movie_range(args.url, args.page, args.movie, args.movie, None, args.delay, True)
        else:
            movies = extract_movie_links(args.url, args.page)
            if movies and args.movie <= len(movies):
                selected = movies[args.movie - 1]
                details = extract_movie_details(selected['url'])
                if details:
                    save_to_json(format_movie_data(details), args.output)
        return

    parser.print_help()

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
