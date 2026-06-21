import json
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

with open('pending_ratings.json', 'r', encoding='utf-8') as f:
    pending = json.load(f)
print(f'Pending: {len(pending)} movies')

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

success = 0
try:
    for item in pending:
        imdb_id = item['imdb_id']
        title = item['title']
        url = f'https://www.imdb.com/title/{imdb_id}/'
        print(f'{title} ({imdb_id})...', end=' ', flush=True)
        driver.get(url)
        time.sleep(3)

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
            print(f'OK {rating}')
            success += 1
        else:
            print('no rating')
finally:
    driver.quit()

print(f'\nSuccess: {success}/{len(pending)}')
