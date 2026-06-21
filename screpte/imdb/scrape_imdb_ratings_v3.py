import json
import re
import os
import time
import requests

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JS_PATH = os.path.join(SCRIPT_DIR, 'data.js')
OMDB_API_KEY = 'dac33e2a'

WIKI_HEADERS = {'User-Agent': 'RachidMovies/1.0 (movie-site; contact@example.com)'}

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

def search_wikipedia(title, year):
    """Search Wikipedia for a movie and return Wikidata item ID"""
    search_query = f'{title} {year} film'
    params = {
        'action': 'query',
        'list': 'search',
        'srsearch': search_query,
        'format': 'json',
        'srlimit': 5
    }
    try:
        r = requests.get(
            'https://en.wikipedia.org/w/api.php',
            params=params,
            headers=WIKI_HEADERS,
            timeout=10
        )
        data = r.json()
        pages = data.get('query', {}).get('search', [])
        for p in pages:
            page_title = p['title']
            params2 = {
                'action': 'query',
                'titles': page_title,
                'prop': 'pageprops',
                'format': 'json'
            }
            r2 = requests.get(
                'https://en.wikipedia.org/w/api.php',
                params=params2,
                headers=WIKI_HEADERS,
                timeout=10
            )
            data2 = r2.json()
            pages2 = data2.get('query', {}).get('pages', {})
            for pid, info in pages2.items():
                if pid == '-1':
                    continue
                props = info.get('pageprops', {})
                wikibase_item = props.get('wikibase_item', '')
                if wikibase_item:
                    return wikibase_item
        return None
    except Exception as e:
        return None

def get_imdb_from_wikidata(wikidata_id):
    """Get IMDB ID from Wikidata entity"""
    url = f'https://www.wikidata.org/wiki/Special:EntityData/{wikidata_id}.json'
    try:
        r = requests.get(url, headers=WIKI_HEADERS, timeout=10)
        data = r.json()
        entity = data.get('entities', {}).get(wikidata_id, {})
        claims = entity.get('claims', {})
        imdb_claim = claims.get('P345', [])
        if imdb_claim:
            imdb_id = imdb_claim[0].get('mainsnak', {}).get('datavalue', {}).get('value', '')
            return imdb_id
        return None
    except Exception as e:
        return None

def get_rating_from_omdb_by_id(imdb_id):
    """Get rating from OMDb using IMDB ID"""
    try:
        r = requests.get(
            'http://www.omdbapi.com/',
            params={'i': imdb_id, 'apikey': OMDB_API_KEY},
            timeout=10
        )
        data = r.json()
        if data.get('Response') == 'True':
            rating = data.get('imdbRating', '')
            if rating and rating != 'N/A':
                return rating, None
        return None, data.get('Error', 'not found')
    except Exception as e:
        return None, str(e)

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
        search_title = clean_title_for_search(title)

        print(f'[{i+1}/{len(data)}] {title} ({year})...', end=' ', flush=True)

        # Step 1: Search Wikipedia
        wikidata_id = search_wikipedia(search_title, year)
        if not wikidata_id:
            print(f'ERR: not on Wikipedia')
            errors += 1
            time.sleep(0.3)
            continue

        print(f'wiki={wikidata_id}...', end=' ', flush=True)

        # Step 2: Get IMDB ID from Wikidata
        imdb_id = get_imdb_from_wikidata(wikidata_id)
        if not imdb_id:
            print(f'ERR: no IMDB ID in Wikidata')
            errors += 1
            time.sleep(0.3)
            continue

        print(f'imdb={imdb_id}...', end=' ', flush=True)

        # Step 3: Get rating from OMDb
        rating_val, err = get_rating_from_omdb_by_id(imdb_id)
        if err or not rating_val:
            print(f'ERR: OMDb: {err}')
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
