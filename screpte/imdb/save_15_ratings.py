import json
import re
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_JS_PATH = os.path.join(SCRIPT_DIR, 'data.js')

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

# Load pending IMDB IDs
pending_path = os.path.join(SCRIPT_DIR, 'pending_ratings.json')
with open(pending_path, 'r', encoding='utf-8') as f:
    pending = json.load(f)
print(f'Pending: {len(pending)} movies')

# Setup Selenium
options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', False)

data, prefix, suffix = load_data_js()
updated = 0
errors = 0

driver = webdriver.Chrome(options=options)
driver.execute_script('Object.defineProperty(navigator, "webdriver", {get: () => undefined})')

try:
    for item in pending:
        idx = item['index']
        imdb_id = item['imdb_id']
        title = item['title']
        
        if (data[idx].get('rating') or '').strip():
            continue
            
        url = f'https://www.imdb.com/title/{imdb_id}/'
        print(f'{title} ({imdb_id})...', end=' ', flush=True)
        driver.get(url)
        time.sleep(2.5)

        rating = None
        scripts = driver.find_elements(By.CSS_SELECTOR, 'script[type="application/ld+json"]')
        for s in scripts:
            content = s.get_attribute('innerHTML') or ''
            m = re.search(r'"ratingValue":\s*([\d.]+)', content)
            if m:
                rating = m.group(1)
                break

        if not rating:
            try:
                el = driver.find_element(By.CSS_SELECTOR, '[data-testid="hero-rating-bar__aggregate-rating__score"]')
                text = el.text.replace('/10', '').replace(',', '.').strip()
                if text:
                    rating = text.split()[0]
            except:
                pass

        if rating:
            data[idx]['rating'] = rating
            updated += 1
            print(f'OK {rating}')
        else:
            errors += 1
            print('no rating')
finally:
    driver.quit()

if updated > 0:
    save_data_js(data, prefix, suffix)

print(f'\nUpdated: {updated} Errors: {errors}')
