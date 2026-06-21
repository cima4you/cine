#!/usr/bin/env python3
"""Convert animerco JSON files to site format and merge into data.js"""
import json, re, os, sys

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JS_PATH = os.path.join(SCRIPT_DIR, 'data.js')
ANIMERCO_DIR = os.path.join(SCRIPT_DIR, 'animerco')

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
    print(f'  data.js: {len(data)} items, {os.path.getsize(DATA_JS_PATH)/1024:.0f} KB')

def normalize(t):
    t = t.strip()
    t = re.sub(r'\s+', '', t)
    for y in [str(x) for x in range(2020, 2030)]:
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
        return True
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

def convert_movie(m):
    return {
        'title': m.get('title', ''),
        'year': m.get('year', ''),
        'rating': m.get('rating', ''),
        'duration': m.get('duration', 'فيلم انمي'),
        'quality': m.get('quality', ''),
        'type': 'انمي',
        'description': m.get('description', ''),
        'cast': [],
        'categories': m.get('categories', []),
        'poster': m.get('poster', ''),
        'servers': [{'name': s['name'], 'url': s['url']} for s in m.get('servers', []) if s.get('url')],
        'downloadServers': [],
        'trial': '',
        'contentType': 'movie',
        'isComplete': True,
    }

def convert_series(a):
    seasons = []
    for s in a.get('seasons', []):
        episodes = []
        for e in s.get('episodes', []):
            episodes.append({
                'episodeNumber': e.get('number', 1),
                'title': e.get('title', ''),
                'duration': '',
                'servers': [{'name': sv['name'], 'url': sv['url']} for sv in e.get('servers', []) if sv.get('url')],
                'downloadServers': [],
            })
        seasons.append({
            'seasonNumber': s.get('season_number', 1),
            'trial': '',
            'description': '',
            'poster': '',
            'episodes': episodes,
        })
    return {
        'title': a.get('title', ''),
        'year': a.get('year', ''),
        'rating': a.get('rating', ''),
        'duration': '',
        'quality': '',
        'type': 'انمي',
        'description': a.get('description', ''),
        'cast': [],
        'categories': a.get('categories', []),
        'poster': a.get('poster', ''),
        'servers': [],
        'downloadServers': [],
        'trial': '',
        'contentType': 'series',
        'isComplete': True,
        'seasons': seasons,
    }

def safe_print(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode('ascii'))

def merge_file(json_path, is_series=False):
    safe_print(f'\n[*] Loading: {json_path}')
    with open(json_path, 'r', encoding='utf-8') as f:
        items = json.load(f)
    safe_print(f'    Items: {len(items)}')

    existing_data, prefix, suffix = load_data_js()
    safe_print(f'    Existing data.js: {len(existing_data)} items')

    added = 0
    skipped = 0
    for item in items:
        converted = convert_series(item) if is_series else convert_movie(item)
        title = converted['title']
        dup = is_duplicate(title, existing_data)
        if dup:
            skipped += 1
        else:
            existing_data.append(converted)
            added += 1

    safe_print(f'    Result: +{added} added, {skipped} skipped, {len(existing_data)} total')

    if added > 0:
        save_data_js(existing_data, prefix, suffix)

    return added, skipped

if __name__ == '__main__':
    total_added = 0
    total_skipped = 0

    # Movies
    m_path = os.path.join(ANIMERCO_DIR, 'results_animerco_movies.json')
    a, s = merge_file(m_path, is_series=False)
    total_added += a
    total_skipped += s

    # Series
    a_path = os.path.join(ANIMERCO_DIR, 'results_animerco_animes.json')
    a, s = merge_file(a_path, is_series=True)
    total_added += a
    total_skipped += s

    print(f'\n[*] TOTAL: {total_added} added, {total_skipped} skipped')
