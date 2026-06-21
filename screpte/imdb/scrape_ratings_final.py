import json
import re
import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JS_PATH = os.path.join(SCRIPT_DIR, 'data.js')
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

def get_rating_selenium(driver, imdb_id):
    try:
        driver.get(f'https://www.imdb.com/title/{imdb_id}/')
        time.sleep(3)
        
        # Try JSON-LD first
        scripts = driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
        for s in scripts:
            content = s.get_attribute('innerHTML') or ''
            m = re.search(r'"ratingValue":\s*([\d.]+)', content)
            if m:
                return m.group(1)
        
        # Try the rating element
        try:
            el = driver.find_element(By.CSS_SELECTOR, '[data-testid="hero-rating-bar__aggregate-rating__score"]')
            text = el.text.replace('/10', '').replace(',', '.').strip()
            parts = text.split()
            if parts:
                return parts[0]
        except:
            pass
            
        return None
    except:
        return None

def main():
    data, prefix, suffix = load_data_js()
    updated = 0
    errors = 0

    movies = [(i, m) for i, m in enumerate(data) if not (m.get('rating') or '').strip()]
    print(f'Movies without rating: {len(movies)}\n')

    # Phase 1: Find IMDB IDs via Wikipedia/Wikidata
    print('=== Wikipedia/Wikidata lookup ===')
    imdb_map = {}
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
                print(f'OK imdb={imdb_id}')
                time.sleep(0.3)
                continue
        print('not found')
        time.sleep(0.3)

    print(f'\nFound {len(imdb_map)} IMDB IDs via Wikipedia\n')

    if not imdb_map:
        print('No IMDB IDs found to scrape')
        return

    # Phase 2: Selenium to get ratings
    print('=== Selenium scraping ===')
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)
    driver.execute_script('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')

    try:
        for idx in list(imdb_map.keys()):
            item = data[idx]
            if (item.get('rating') or '').strip():
                continue
            imdb_id = imdb_map[idx]
            title = item.get('title','')
            print(f'  {title} (tt{imdb_id})...', end=' ', flush=True)
            rating = get_rating_selenium(driver, imdb_id)
            if rating:
                data[idx]['rating'] = rating
                updated += 1
                print(f'{rating}')
            else:
                errors += 1
                print('FAIL')
    finally:
        driver.quit()

    if updated > 0:
        save_data_js(data, prefix, suffix)

    print(f'\nDone. Updated={updated} Errors={errors}')

if __name__ == '__main__':
    main()
