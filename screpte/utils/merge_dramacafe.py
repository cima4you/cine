#!/usr/bin/env python3
"""Merge dramacafe scraped results into data.js.
Handles both flat movie format and nested series format.

Usage: python scripts/utils/merge_dramacafe.py
"""
import json, os, glob, re

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_JS_PATH = os.path.join(SCRIPT_DIR, 'data.js')
INPUT_DIR = os.path.join(SCRIPT_DIR, 'scripts', 'dramacafe', 'data')

RE_SPACES = re.compile(r'\s+')
RE_YEAR = re.compile(r'20[12][0-9]')
RE_FILM = re.compile(r'^فيلم')
RE_FALAM = re.compile(r'^فلم')
RE_TASHKEEL = re.compile(r'[\u064B-\u0652]')
RE_CLEAN_TITLE = re.compile(r'فيلم|فلم|مسلسل|مترجم|اون\s*لاين|أون\s*لاين|اون-لاين|عربي|مدبلج|HD', flags=re.IGNORECASE)
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
    t = RE_FILM.sub('', t)
    t = RE_FALAM.sub('', t)
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


def transform_movie(film):
    """Transform flat movie format to data.js format."""
    servers_list = []
    urls = film.get('servers', [])
    names = film.get('server_names', [])
    for i, (url, name) in enumerate(zip(urls, names)):
        entry = {'name': name, 'url': url}
        if i == 0:
            entry['isDefault'] = True
        servers_list.append(entry)
    if not servers_list:
        servers_list = [{'name': 'Source', 'url': film.get('source', ''), 'isDefault': True}]

    return {
        'title': clean_title(film.get('title', '')),
        'year': film.get('year', ''),
        'rating': '',
        'duration': film.get('duration', ''),
        'quality': '',
        'type': film_type,
        'description': film.get('description', ''),
        'cast': [],
        'categories': [c for c in film.get('categories', [])],
        'poster': film.get('image', ''),
        'servers': servers_list,
        'downloadServers': [],
        'trial': '',
        'contentType': 'movie',
    }


# Main
pattern = os.path.join(INPUT_DIR, 'results_dramacafe_*.json')
files = glob.glob(pattern)
files = [f for f in files if not f.endswith('results_dramacafe_all.json')]

if not files:
    print('No results_dramacafe_*.json files found in', INPUT_DIR)
    print('Run scrape_dramacafe.py first.')
    exit()

print(f'Found {len(files)} type files:')
for f in files:
    print('  ' + os.path.basename(f))

existing_data, prefix, suffix = load_data_js()
before = len(existing_data)

print(f'Building index for {len(existing_data)} existing items...')
norm_map, norm_set = build_norm_index(existing_data)
print('Index built.')

total_added = 0
total_skipped = 0

for filepath in sorted(files):
    basename = os.path.basename(filepath)
    film_type = basename.replace('results_dramacafe_', '').replace('.json', '')
    print(f'\n--- {film_type} ({basename}) ---')

    with open(filepath, 'r', encoding='utf-8') as f:
        entries = json.load(f)

    added = 0
    skipped = 0
    for entry in entries:
        # Detect format
        if entry.get('contentType') == 'series' or 'seasons' in entry:
            # Series format — already in data.js shape, use directly
            transformed = entry
        else:
            # Movie format — needs transformation
            transformed = transform_movie(entry)

        dup = is_duplicate_fast(transformed.get('title', ''), norm_map, norm_set, existing_data)
        if dup:
            skipped += 1
        else:
            existing_data.append(transformed)
            new_norm = normalize(transformed.get('title', ''))
            norm_map.append(new_norm)
            norm_set.add(new_norm)
            added += 1

    print(f'  Added: {added}, Skipped: {skipped}')
    total_added += added
    total_skipped += skipped

if total_added > 0:
    save_data_js(existing_data, prefix, suffix)
else:
    print('\nNo new items to add.')

print(f'\nTotal: +{total_added} added, {total_skipped} skipped, {before} before, {len(existing_data)} now')
print('Usage: python scripts/utils/merge_dramacafe.py')
