import json
import re
import os
import sys
import time
import base64
import requests

sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup
from urllib.parse import urljoin

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JS_PATH = os.path.join(SCRIPT_DIR, 'data.js')
BASE_URL = "https://www.tuktukhd.com"
CATEGORY_URL = f"{BASE_URL}/category/movies-2/%D8%A7%D9%81%D9%84%D8%A7%D9%85-%D9%87%D9%86%D8%AF%D9%89/"

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
    'Accept-Language': 'ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7'
})

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
    print(f'  data.js: {len(data)} items, {size/1024:.0f} KB')

def extract_detail_urls():
    mapping = {}
    page = 1
    while True:
        url = f'{CATEGORY_URL}?page={page}'
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            items = soup.select('div.Block--Item a')
            if not items:
                break
            for item in items:
                href = item.get('href')
                title = item.get('title')
                if href and title:
                    full_url = urljoin(BASE_URL, href) if not href.startswith('http') else href
                    mapping[normalize(title)] = full_url
            page += 1
            time.sleep(0.5)
        except Exception as e:
            print(f'  توقف في الصفحة {page}: {e}')
            break
    print(f'  تم جمع {len(mapping)} رابط من {page-1} صفحات')
    return mapping

def fix_movie(item, detail_url):
    try:
        resp = session.get(detail_url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        iframe = soup.select_one('iframe[data-crypt]')
        video_url = ''
        if iframe:
            crypt = iframe.get('data-crypt')
            if crypt:
                try:
                    video_url = base64.b64decode(crypt).decode('utf-8')
                except:
                    pass
        if not video_url:
            iframe2 = soup.select_one('div.player--iframe iframe[src]')
            if iframe2:
                src = iframe2.get('src', '')
                if src and 'blob:' not in src:
                    video_url = src

        if video_url:
            new_servers = [{'name': 'TukTuk Vip', 'url': video_url, 'isDefault': True}]
            if item.get('servers') != new_servers:
                item['servers'] = new_servers
                return True

        poster = ''
        poster_el = soup.select_one('div.Poster--Block img')
        if poster_el:
            poster = poster_el.get('data-src') or poster_el.get('src') or ''
        if not poster or 'no.png' in poster:
            og = soup.select_one('meta[property="og:image"]')
            if og:
                poster = og.get('content', '')
        if poster and 'no.png' not in poster:
            item['poster'] = poster

        download_servers = []
        for a in soup.select('a[data-real-url]'):
            real_url = a.get('data-real-url')
            name_el = a.select_one('div.download--item span') or a.select_one('span')
            name = name_el.text.strip() if name_el else 'Download'
            if real_url:
                download_servers.append({'name': name, 'url': real_url})
        if download_servers:
            item['downloadServers'] = download_servers

        details_el = soup.select_one('div.story')
        if details_el:
            item['description'] = details_el.text.strip()

        cats = [a.text.strip() for a in soup.select('div.catssection a')]
        if cats:
            item['categories'] = cats

        # quality, year, duration, rating from RightTaxContent
        for li in soup.select('ul.RightTaxContent li'):
            span = li.select_one('span')
            if not span:
                continue
            key = span.text.strip().rstrip(':').strip()
            vals = [c.text.strip() for c in li.find_all(['a', 'strong'])]
            val = ' '.join(vals)
            if key == 'جودة الفيلم':
                item['quality'] = val
            elif key == 'موعد الصدور':
                item['year'] = val
            elif key == 'توقيت الفيلم':
                item['duration'] = val
            elif key == 'تقييم الفيلم':
                item['rating'] = val

        return False
    except Exception as e:
        print(f'    خطأ: {e}')
        return False

def main():
    data, prefix, suffix = load_data_js()
    print(f'data.js: {len(data)} items')

    print('\nجمع روابط التفاصيل من توك توك...')
    mapping = extract_detail_urls()

    fixed = 0
    skipped = 0
    not_found = 0
    for i, item in enumerate(data):
        title = item.get('title', '')
        if not title:
            continue

        norm = normalize(title)
        detail_url = mapping.get(norm)
        if not detail_url:
            # try partial match
            for key, url in mapping.items():
                if norm in key or key in norm:
                    detail_url = url
                    break
        if not detail_url:
            not_found += 1
            continue

        print(f'  [{i+1}/{len(data)}] {title}')
        updated = fix_movie(item, detail_url)
        if updated:
            fixed += 1
            print(f'    ✓ تم تحديث رابط المشاهدة')
        else:
            skipped += 1

        time.sleep(0.3)

    if fixed > 0:
        save_data_js(data, prefix, suffix)

    print(f'\nتم: {fixed} محدث | {skipped} بدون تغيير | {not_found} غير موجود')
    print(f'المجموع: {len(data)}')

if __name__ == '__main__':
    main()
