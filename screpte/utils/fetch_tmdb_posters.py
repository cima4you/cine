#!/usr/bin/env python3
"""
Fetch poster URLs from TMDB for all foreign movies in data.js.
Usage: python fetch_tmdb_posters.py
"""
import json, os, sys, requests, time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.stdout.reconfigure(encoding='utf-8')

API_KEY = '0301bf9dd3a630dcbbea37f5c2b07d3e'
BASE = 'https://api.themoviedb.org/3'

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data.js')

print('جارٍ تحميل data.js...', flush=True)
with open(DATA_DIR, 'r', encoding='utf-8') as f:
    content = f.read()
arr_start = content.index('[')
arr_end = content.rindex(']') + 1
data = json.loads(content[arr_start:arr_end])
prefix = content[:arr_start]
suffix = content[arr_end:]

# Get foreign movies
foreign = [(i, x) for i, x in enumerate(data) if x.get('type') == 'أجنبي']
print(f'إجمالي الأفلام الأجنبية: {len(foreign)}')

import re as _re

def clean_title(title):
    """Extract year and clean title."""
    title = title.strip()
    m = _re.search(r'\s+(19\d\d|20\d\d)$', title)
    year = m.group(1) if m else None
    if year:
        title = title[:m.start()].strip()
    # Remove HTML entities
    title = _re.sub(r'&#\d+;', '', title)
    title = _re.sub(r'&[a-z]+;', ' ', title)
    return title, year

def fetch_poster(idx, item):
    raw_title = item['title'].strip()
    title, year = clean_title(raw_title)
    
    try:
        params = {'api_key': API_KEY, 'query': title, 'language': 'en-US'}
        if year:
            params['primary_release_year'] = year
        
        r = requests.get(f'{BASE}/search/movie', params=params, timeout=10)
        if r.status_code != 200:
            return idx, None, f'HTTP {r.status_code}'
        
        results = r.json().get('results', [])
        if not results:
            return idx, None, 'no results'
        
        # Look for exact match
        best = None
        raw_lower = raw_title.lower()
        for m in results:
            mt = m['title'].strip().lower()
            if mt == raw_lower:
                best = m
                break
            # Also check if main title matches
            mt_clean, _ = clean_title(m['title'])
            if mt_clean.lower() == title.lower():
                best = m
                break
        
        if not best:
            best = results[0]
        
        poster = best.get('poster_path')
        if poster:
            url = f'https://image.tmdb.org/t/p/w500{poster}'
            return idx, url, None
        else:
            return idx, None, 'no poster_path'
    except Exception as e:
        return idx, None, str(e)

found = 0
not_found = 0
errors = 0
total = len(foreign)

print('جاري جلب البوسترات...')
with ThreadPoolExecutor(max_workers=10) as ex:
    futures = {ex.submit(fetch_poster, i, x): i for i, x in foreign}
    for fut in as_completed(futures):
        idx, url, err = fut.result()
        if url:
            data[idx]['poster'] = url
            found += 1
        elif err:
            if err in ('no results', 'no poster_path'):
                not_found += 1
            else:
                errors += 1
        if (found + not_found + errors) % 200 == 0:
            print(f'  {found+not_found+errors}/{total}: found={found}, not_found={not_found}, errors={errors}')

print(f'\nتم: found={found}, not_found={not_found}, errors={errors} من {total}')

# Save
json_str = json.dumps(data, ensure_ascii=False)
with open(DATA_DIR, 'w', encoding='utf-8') as f:
    f.write(prefix + json_str + suffix)
print(f'تم حفظ {len(data)} عنصر في data.js')
