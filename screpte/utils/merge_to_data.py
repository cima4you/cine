import json
import re
import os
import argparse

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_JS_PATH = os.path.join(SCRIPT_DIR, 'data.js')

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

def clean_title(raw):
    t = re.sub(r'فيلم|فلم|مسلسل|مترجم|اون\s*لاين|أون\s*لاين|اون-لاين|عربي|مدبلج', '', raw, flags=re.IGNORECASE).strip()
    t = re.sub(r'[\u0600-\u06FF]+', '', t).strip()
    t = re.sub(r'\s{2,}', ' ', t).strip()
    t = re.sub(r'^[\s\-,;:.]+|[\s\-,;:.]+$', '', t).strip()
    return t if t else raw

def transform_film(film):
    details = film.get('info', {}).get('details', {})
    title = clean_title(film.get('titre', ''))

    watch_servers = film.get('servers', {}).get('watch', [])
    if isinstance(watch_servers, list):
        servers = []
        for s in watch_servers:
            servers.append({
                "name": s.get('name', 'Server'),
                "url": s.get('url', ''),
                "isDefault": s.get('isDefault', False)
            })
    elif isinstance(watch_servers, str):
        servers = [{"name": "TukTuk", "url": watch_servers, "isDefault": True}]
    else:
        servers = []

    download_servers_raw = film.get('servers', {}).get('download', [])
    if isinstance(download_servers_raw, list):
        download_servers = []
        for s in download_servers_raw:
            download_servers.append({
                "name": s.get('name', 'Download'),
                "url": s.get('url', '')
            })
    elif isinstance(download_servers_raw, str):
        download_servers = [{"name": "الرسمي", "url": download_servers_raw}]
    else:
        download_servers = []

    cast_raw = details.get('بطولة :', '')
    cast = [a.strip() for a in re.split(r'[-–—,/\n]+', cast_raw) if a.strip()] if cast_raw else []

    categories = film.get('info', {}).get('catssection', [])

    return {
        "title": title,
        "year": details.get('موعد الصدور :', ''),
        "rating": details.get('تقييم الفيلم :', ''),
        "duration": details.get('توقيت الفيلم :', ''),
        "quality": details.get('جودة الفيلم :', ''),
        "type": DEFAULT_TYPE,
        "description": film.get('info', {}).get('story', ''),
        "cast": cast,
        "categories": categories,
        "poster": film.get('image', ''),
        "servers": servers,
        "downloadServers": download_servers,
        "trial": "",
        "contentType": "movie"
    }

def merge_results(input_file):
    input_path = os.path.join(SCRIPT_DIR, input_file) if not os.path.isabs(input_file) else input_file
    with open(input_path, 'r', encoding='utf-8') as f:
        new_films = json.load(f)

    existing_data, prefix, suffix = load_data_js()

    added = 0
    skipped = 0
    for film in new_films:
        transformed = transform_film(film)
        dup = is_duplicate(transformed['title'], existing_data)
        if dup:
            print(f'  {transformed["title"]}')
            skipped += 1
        else:
            existing_data.append(transformed)
            added += 1
            print(f'  + {transformed["title"]}')

    if added > 0:
        save_data_js(existing_data, prefix, suffix)

    print(f'\n  Skipped: {skipped} | Added: {added} | Total: {len(existing_data)}')

DEFAULT_TYPE = 'هندي'

def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('input', help='results.json')
    parser.add_argument('--type', default='هندي', help='نوع الفيلم: هندي, أجنبي, عربي, إلخ')
    args = parser.parse_args()

    global DEFAULT_TYPE
    DEFAULT_TYPE = args.type
    merge_results(args.input)

if __name__ == '__main__':
    main()
