#!/usr/bin/env python3
"""Merge egydead series results into data.js.

Usage: python scripts/utils/merge_egydead_series.py
"""
import json, os, re

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_JS_PATH = os.path.join(SCRIPT_DIR, 'data.js')
INPUT_FILE = os.path.join(SCRIPT_DIR, 'data_egydead_series.json')

RE_SPACES = re.compile(r'\s+')
RE_YEAR = re.compile(r'20[12][0-9]')
RE_TASHKEEL = re.compile(r'[\u064B-\u0652]')
RE_CLEAN_TITLE = re.compile(r'مسلسل|مترجم|اون\s*لاين|أون\s*لاين|HD|الموسم\s*الاول|الموسم\s*الثاني|الحلقة', flags=re.IGNORECASE)
RE_ARABIC = re.compile(r'[\u0600-\u06FF]+')
RE_MULTI_SPACE = re.compile(r'\s{2,}')
RE_EDGES = re.compile(r'^[\s\-,;:.]+|[\s\-,;:.]+$')


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
    print(f'  data.js: {len(data)} items, {size // 1024} KB')


def normalize(t):
    if not t:
        return ''
    t = t.strip()
    t = RE_SPACES.sub('', t)
    t = RE_YEAR.sub('', t)
    t = t.strip()
    t = RE_TASHKEEL.sub('', t)
    return t.lower()


def build_norm_index(existing_data):
    norm_map = []
    norm_set = set()
    for item in existing_data:
        n = normalize(item.get('title', ''))
        norm_map.append(n)
        norm_set.add(n)
    return norm_map, norm_set


def is_duplicate_fast(new_title, norm_map, norm_set, existing_data):
    new_norm = normalize(new_title)
    if not new_norm:
        return None
    if new_norm in norm_set:
        for i, n in enumerate(norm_map):
            if n == new_norm:
                return existing_data[i]
    for i, existing_norm in enumerate(norm_map):
        if not existing_norm:
            continue
        if new_norm in existing_norm or existing_norm in new_norm:
            longer = max(len(new_norm), len(existing_norm))
            shorter = min(len(new_norm), len(existing_norm))
            if shorter > 0 and longer / shorter < 1.3:
                return existing_data[i]
    return None


def clean_title(raw):
    t = RE_CLEAN_TITLE.sub('', raw).strip()
    t = RE_ARABIC.sub('', t).strip()
    t = RE_MULTI_SPACE.sub(' ', t).strip()
    t = RE_EDGES.sub('', t).strip()
    return t if t else raw


def transform_series(series):
    """Transform egydead series format to data.js format."""
    title = clean_title(series.get('title', ''))
    if not title:
        title = series.get('_slug', '').replace('-', ' ').title()

    servers = series.get('servers', [])
    if not servers:
        servers = [{'name': 'server1', 'url': '', 'isDefault': True}]

    categories = series.get('categories', [])
    if not categories:
        categories = ['دراما']

    return {
        'title': title,
        'year': series.get('year', ''),
        'rating': series.get('rating', ''),
        'duration': series.get('duration', ''),
        'quality': series.get('quality', 'WEB-DL'),
        'type': series.get('type', 'تركي'),
        'description': series.get('description', ''),
        'cast': series.get('cast', [' ']),
        'categories': categories,
        'poster': series.get('poster', ''),
        'servers': servers,
        'downloadServers': series.get('downloadServers', []),
        'trial': series.get('trial', ''),
        'contentType': series.get('contentType', 'series'),
    }


# Main
if not os.path.exists(INPUT_FILE):
    print(f'File not found: {INPUT_FILE}')
    print('Run scrape_egydead_series.py first.')
    exit()

with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    new_series = json.load(f)

print(f'Found {len(new_series)} series in {os.path.basename(INPUT_FILE)}')

existing_data, prefix, suffix = load_data_js()
before = len(existing_data)

print(f'Building index for {len(existing_data)} existing items...')
norm_map, norm_set = build_norm_index(existing_data)
print('Index built.')

added = 0
skipped = 0

for series in new_series:
    transformed = transform_series(series)
    dup = is_duplicate_fast(transformed['title'], norm_map, norm_set, existing_data)
    if dup:
        skipped += 1
    else:
        existing_data.append(transformed)
        new_norm = normalize(transformed['title'])
        norm_map.append(new_norm)
        norm_set.add(new_norm)
        added += 1

if added > 0:
    save_data_js(existing_data, prefix, suffix)
else:
    print('\nNo new items to add.')

print(f'\nTotal: +{added} added, {skipped} skipped, {before} before, {len(existing_data)} now')
print('Usage: python scripts/utils/merge_egydead_series.py')
