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
    return t if t else raw_title

def fetch_rating_omdb(title, year):
    search_title = clean_title_for_search(title)
    if not search_title:
        return None, 'empty title after cleanup'

    try:
        r = requests.get(
            'http://www.omdbapi.com/',
            params={'t': search_title, 'y': year, 'apikey': OMDB_API_KEY},
            timeout=10
        )
        data = r.json()
        if data.get('Response') == 'True':
            imdb_rating = data.get('imdbRating', '')
            if imdb_rating and imdb_rating != 'N/A':
                return imdb_rating, None
            return None, 'no rating in response'
        else:
            error = data.get('Error', 'unknown error')
            return None, error
    except Exception as e:
        return None, str(e)

def main():
    data, prefix, suffix = load_data_js()

    updated = 0
    skipped = 0
    errors = 0

    for i, item in enumerate(data):
        rating = (item.get('rating') or '').strip()
        if rating:
            skipped += 1
            continue

        title = item.get('title', '')
        year = item.get('year', '')

        print(f'[{i+1}/{len(data)}] {title} ({year})...', end=' ', flush=True)

        rating_val, err = fetch_rating_omdb(title, year)
        if err or not rating_val:
            print(f'ERR: {err}')
            errors += 1
            time.sleep(1)
            continue

        item['rating'] = rating_val
        updated += 1
        print(f'OK rating={rating_val}')

        time.sleep(0.5)

    if updated > 0:
        save_data_js(data, prefix, suffix)

    print(f'\nDone. Updated: {updated} | Skipped: {skipped} | Errors: {errors}')

if __name__ == '__main__':
    main()
