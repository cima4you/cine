import json
import re
import os
import time
import requests

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JS_PATH = os.path.join(SCRIPT_DIR, 'data.js')
OMDB_API_KEY = 'dac33e2a'

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
    print(f'  data.js saved: {len(data)} items')

def clean_title_for_search(raw_title):
    t = re.sub(r'[\u0600-\u06FF]+', '', raw_title).strip()
    t = re.sub(r'\s*\d{4}\s*$', '', t).strip()
    t = re.sub(r'\s{2,}', ' ', t).strip()
    t = re.sub(r'[^\w\s\-:,.!?\'()]', '', t).strip()
    return t if t else raw_title

def try_omdb_direct(title, year):
    """Try direct title lookup (exact match)"""
    try:
        r = requests.get(
            'http://www.omdbapi.com/',
            params={'t': title, 'y': year, 'apikey': OMDB_API_KEY},
            timeout=10
        )
        data = r.json()
        if data.get('Response') == 'True':
            imdb_rating = data.get('imdbRating', '')
            if imdb_rating and imdb_rating != 'N/A':
                return imdb_rating, None
        return None, data.get('Error', 'not found')
    except Exception as e:
        return None, str(e)

def try_omdb_search(title, year):
    """Try search endpoint and match by year"""
    try:
        r = requests.get(
            'http://www.omdbapi.com/',
            params={'s': title, 'apikey': OMDB_API_KEY},
            timeout=10
        )
        data = r.json()
        if data.get('Response') == 'True':
            results = data.get('Search', [])
            # Try to match by year first
            if year:
                for m in results:
                    if m.get('Year') == year:
                        imdb_id = m.get('imdbID', '')
                        if imdb_id:
                            # Get full details
                            r2 = requests.get(
                                'http://www.omdbapi.com/',
                                params={'i': imdb_id, 'apikey': OMDB_API_KEY},
                                timeout=10
                            )
                            detail = r2.json()
                            rating = detail.get('imdbRating', '')
                            if rating and rating != 'N/A':
                                return rating, None
            # Fallback: try first result
            if results:
                imdb_id = results[0].get('imdbID', '')
                if imdb_id:
                    r2 = requests.get(
                        'http://www.omdbapi.com/',
                        params={'i': imdb_id, 'apikey': OMDB_API_KEY},
                        timeout=10
                    )
                    detail = r2.json()
                    rating = detail.get('imdbRating', '')
                    if rating and rating != 'N/A':
                        return rating, None
        return None, 'search returned nothing'
    except Exception as e:
        return None, str(e)

def try_omdb_no_year(title):
    """Try direct lookup without year"""
    try:
        r = requests.get(
            'http://www.omdbapi.com/',
            params={'t': title, 'apikey': OMDB_API_KEY},
            timeout=10
        )
        data = r.json()
        if data.get('Response') == 'True':
            imdb_rating = data.get('imdbRating', '')
            if imdb_rating and imdb_rating != 'N/A':
                return imdb_rating, None
        return None, data.get('Error', 'not found')
    except Exception as e:
        return None, str(e)

def fetch_rating_multimethod(raw_title, year):
    search_title = clean_title_for_search(raw_title)
    if not search_title:
        return None, 'empty title'

    # Method 1: Direct + year
    rating, err = try_omdb_direct(search_title, year)
    if rating:
        return rating, None

    # Method 2: Direct without year
    rating, err = try_omdb_no_year(search_title)
    if rating:
        return rating, None

    # Method 3: Search + year match
    rating, err = try_omdb_search(search_title, year)
    if rating:
        return rating, None

    # Method 4: Truncate long titles (take first 3 words)
    words = search_title.split()
    if len(words) > 3:
        short_title = ' '.join(words[:3])
        rating, err = try_omdb_direct(short_title, year)
        if rating:
            return rating, None
        rating, err = try_omdb_no_year(short_title)
        if rating:
            return rating, None
        rating, err = try_omdb_search(short_title, year)
        if rating:
            return rating, None

    return None, 'all methods failed'

def main():
    data, prefix, suffix = load_data_js()

    updated = 0
    already_have = 0
    errors = 0
    total_no_rating = sum(1 for m in data if not (m.get('rating') or '').strip())
    print(f'Movies without rating: {total_no_rating}\n')

    for i, item in enumerate(data):
        rating = (item.get('rating') or '').strip()
        if rating:
            already_have += 1
            continue

        title = item.get('title', '')
        year = item.get('year', '')

        print(f'[{i+1}/{len(data)}] {title} ({year})...', end=' ', flush=True)

        rating_val, err = fetch_rating_multimethod(title, year)
        if err or not rating_val:
            print(f'ERR: {err}')
            errors += 1
            time.sleep(0.3)
            continue

        item['rating'] = rating_val
        updated += 1
        print(f'OK rating={rating_val}')

        time.sleep(0.5)

    if updated > 0:
        save_data_js(data, prefix, suffix)

    print(f'\nDone. Updated: {updated} | Already had: {already_have} | Errors: {errors}')

if __name__ == '__main__':
    main()
