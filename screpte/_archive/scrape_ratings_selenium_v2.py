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
WIKI_HEADERS = {'User-Agent': 'RachidMovies/1.0'}

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

def clean_title(t):
    t = re.sub(r'[\u0600-\u06FF]+', '', t).strip()
    t = re.sub(r'\s*\d{4}\s*$', '', t).strip()
    return re.sub(r'\s{2,}', ' ', t).strip() or t

def search_wikipedia(title, year):
    q = f'{title} {year} film'
    try:
        r = requests.get('https://en.wikipedia.org/w/api.php',
            params={'action':'query','list':'search','srsearch':q,'format':'json','srlimit':3},
            headers=WIKI_HEADERS, timeout=10)
        for p in r.json().get('query',{}).get('search',[]):
            r2 = requests.get('https://en.wikipedia.org/w/api.php',
                params={'action':'query','titles':p['title'],'prop':'pageprops','format':'json'},
                headers=WIKI_HEADERS, timeout=10)
            for pid, info in r2.json().get('query',{}).get('pages',{}).items():
                wb = info.get('pageprops',{}).get('wikibase_item','')
                if wb and pid != '-1':
                    return wb
    except:
        pass
    return None

def get_imdb_from_wikidata(wid):
    try:
        r = requests.get(f'https://www.wikidata.org/wiki/Special:EntityData/{wid}.json',
            headers=WIKI_HEADERS, timeout=10)
        claims = r.json().get('entities',{}).get(wid,{}).get('claims',{})
        claim = claims.get('P345',[])
        if claim:
            return claim[0]['mainsnak']['datavalue']['value']
    except:
        pass
    return None

def get_rating_from_page(driver, url):
    try:
        driver.get(url)
        time.sleep(2.5)
        # JSON-LD
        for s in driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]'):
            m = re.search(r'"ratingValue":\s*"?([\d.]+)"?', s.get_attribute('innerHTML') or '')
            if m: return m.group(1)
        # Rating element
        try:
            el = driver.find_element(By.CSS_SELECTOR, '[data-testid="hero-rating-bar__aggregate-rating__score"]')
            t = el.text.replace('/10','').replace(',','.').strip()
            if t: return t
        except:
            pass
        return None
    except:
        return None

def main():
    data, prefix, suffix = load_data_js()
    updated = 0
    errors = 0

    # Find movies without rating
    movies = [(i, m) for i, m in enumerate(data) if not (m.get('rating') or '').strip()]
    print(f'Movies without rating: {len(movies)}\n')

    # === Phase 1: Find IMDB IDs via Wikipedia/Wikidata (no Selenium) ===
    print('=== Phase 1: Wikipedia/Wikidata lookup ===')
    imdb_map = {}  # index -> imdb_id
    for idx, item in movies:
        title = item.get('title','')
        year = item.get('year','')
        stitle = clean_title(title)
        print(f'  {stitle} ({year})...', end=' ', flush=True)
        wid = search_wikipedia(stitle, year)
        if wid:
            imdb_id = get_imdb_from_wikidata(wid)
            if imdb_id and re.match(r'^tt\d+$', imdb_id):
                imdb_map[idx] = imdb_id
                print(f'wiki imdb={imdb_id}')
                time.sleep(0.3)
                continue
        print('not found')
        time.sleep(0.3)

    print(f'\nFound IMDB IDs for {len(imdb_map)} movies via Wikipedia\n')

    # === Phase 2: Use Selenium to scrape ratings ===
    print('=== Phase 2: Selenium scraping ===')
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    try:
        # First: scrape movies with known IMDB IDs (fast)
        for idx, item in movies:
            if idx not in imdb_map:
                continue
            if (item.get('rating') or '').strip():
                continue
            title = item.get('title','')
            imdb_id = imdb_map[idx]
            print(f'  {title} ({imdb_id})...', end=' ', flush=True)
            rating = get_rating_from_page(driver, f'https://www.imdb.com/title/{imdb_id}/')
            if rating:
                data[idx]['rating'] = rating
                updated += 1
                print(f'{rating}')
            else:
                errors += 1
                print('FAIL')

        # Second: try IMDB search for remaining movies
        for idx, item in movies:
            if (item.get('rating') or '').strip():
                continue
            title = item.get('title','')
            year = item.get('year','')
            stitle = clean_title(title)
            print(f'  search: {stitle} ({year})...', end=' ', flush=True)
            try:
                driver.get(f'https://www.imdb.com/find/?q={stitle.replace(" ","+")}')
                time.sleep(2.5)
                # Try to find and click first result
                try:
                    link = driver.find_element(By.CSS_SELECTOR, '[data-testid="find-results-section-title"] a')
                    href = link.get_attribute('href')
                    if href and '/title/tt' in href:
                        imdb_id = re.search(r'/title/(tt\d+)/', href).group(1)
                        rating = get_rating_from_page(driver, f'https://www.imdb.com/title/{imdb_id}/')
                        if rating:
                            data[idx]['rating'] = rating
                            updated += 1
                            print(f'{rating}')
                        else:
                            errors += 1
                            print('no rating on page')
                    else:
                        errors += 1
                        print('no imdb link')
                except:
                    errors += 1
                    print('search no results')
            except Exception as e:
                errors += 1
                print(f'ERR: {str(e)[:40]}')
    finally:
        driver.quit()

    if updated > 0:
        save_data_js(data, prefix, suffix)

    print(f'\nTotal: Updated={updated} Errors={errors} Remaining={len(movies)-updated-errors}')

if __name__ == '__main__':
    main()
