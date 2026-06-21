import json
import re
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    search_query = f'{title} {year} film'
    params = {
        'action': 'query',
        'list': 'search',
        'srsearch': search_query,
        'format': 'json',
        'srlimit': 5
    }
    try:
        r = requests.get('https://en.wikipedia.org/w/api.php', params=params, headers=WIKI_HEADERS, timeout=10)
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
            r2 = requests.get('https://en.wikipedia.org/w/api.php', params=params2, headers=WIKI_HEADERS, timeout=10)
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

def get_rating_via_selenium(driver, imdb_id):
    try:
        url = f'https://www.imdb.com/title/{imdb_id}/'
        driver.get(url)
        time.sleep(3)

        # Try JSON-LD first
        try:
            scripts = driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
            for script in scripts:
                content = script.get_attribute('innerHTML') or ''
                match = re.search(r'"ratingValue":\s*"?([\d.]+)"?', content)
                if match:
                    return match.group(1), None
        except:
            pass

        # Try the rating element
        try:
            el = driver.find_element(By.CSS_SELECTOR, 'div[data-testid="hero-rating-bar__aggregate-rating__score"]')
            text = el.text.replace('/10', '').replace(',', '.').strip()
            if text:
                return text, None
        except:
            pass

        # Try any script containing ratingValue
        try:
            scripts = driver.find_elements(By.TAG_NAME, 'script')
            for script in scripts:
                html = script.get_attribute('innerHTML') or ''
                if 'ratingValue' in html:
                    match = re.search(r'"ratingValue":\s*"?([\d.]+)"?', html)
                    if match:
                        return match.group(1), None
        except:
            pass

        return None, 'no rating found'
    except Exception as e:
        return None, str(e)

def main():
    data, prefix, suffix = load_data_js()

    updated = 0
    already_have = 0
    errors = 0
    total_no_rating = sum(1 for m in data if not (m.get('rating') or '').strip())
    print(f'Movies without rating: {total_no_rating}\n')

    # Setup Selenium
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')

    print('Starting Chrome...')
    driver = webdriver.Chrome(options=options)
    print('Chrome started.\n')

    try:
        for i, item in enumerate(data):
            rating = (item.get('rating') or '').strip()
            if rating:
                already_have += 1
                continue

            title = item.get('title', '')
            year = item.get('year', '')
            search_title = clean_title_for_search(title)

            print(f'[{i+1}/{len(data)}] {title} ({year})...', end=' ', flush=True)

            # Method 1: Try OMDb first (might work if rate limit reset)
            rating_val, err = try_omdb(search_title, year)
            if rating_val:
                item['rating'] = rating_val
                updated += 1
                print(f'OMDb: {rating_val}')
                time.sleep(0.3)
                continue

            # Method 2: Wikipedia -> Wikidata -> OMDb
            wikidata_id = search_wikipedia(search_title, year)
            if wikidata_id:
                imdb_id = get_imdb_from_wikidata(wikidata_id)
                if imdb_id:
                    # Try OMDb by ID
                    rating_val, err = try_omdb_by_id(imdb_id)
                    if rating_val:
                        item['rating'] = rating_val
                        updated += 1
                        print(f'Wiki+OMDb: {rating_val}')
                        time.sleep(0.3)
                        continue

                    # Method 3: Selenium for IMDB rating
                    rating_val, err = get_rating_via_selenium(driver, imdb_id)
                    if rating_val:
                        item['rating'] = rating_val
                        updated += 1
                        print(f'Selenium: {rating_val}')
                        continue

                    print(f'Selenium err: {err}')
                    errors += 1
                    continue

            print(f'ERR: not found')
            errors += 1
            time.sleep(0.3)

    finally:
        driver.quit()

    if updated > 0:
        save_data_js(data, prefix, suffix)

    print(f'\nDone. Updated: {updated} | Already had: {already_have} | Errors: {errors}')

def try_omdb(title, year):
    search_title = clean_title_for_search(title)
    if not search_title:
        return None, 'empty'
    try:
        r = requests.get('http://www.omdbapi.com/', params={'t': search_title, 'y': year, 'apikey': OMDB_API_KEY}, timeout=10)
        data = r.json()
        if data.get('Response') == 'True':
            rating = data.get('imdbRating', '')
            if rating and rating != 'N/A':
                return rating, None
            return None, 'no rating'
        return None, data.get('Error', 'not found')
    except Exception as e:
        return None, str(e)

def try_omdb_by_id(imdb_id):
    try:
        r = requests.get('http://www.omdbapi.com/', params={'i': imdb_id, 'apikey': OMDB_API_KEY}, timeout=10)
        data = r.json()
        if data.get('Response') == 'True':
            rating = data.get('imdbRating', '')
            if rating and rating != 'N/A':
                return rating, None
            return None, 'no rating'
        return None, data.get('Error', 'not found')
    except Exception as e:
        return None, str(e)

if __name__ == '__main__':
    main()
