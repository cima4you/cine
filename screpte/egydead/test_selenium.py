import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import re, time, shutil, os

# Clear cached chromedriver if version mismatch
cache_dir = os.path.expanduser('~/.undetected_chromedriver')
if os.path.exists(cache_dir):
    shutil.rmtree(cache_dir)

driver = uc.Chrome(headless=True, version_main=148)
driver.get('https://tv8.egydead.live/')
time.sleep(3)
html = driver.page_source
print('Page loaded, length:', len(html))
print('Blocked:', 'Just a moment' in html or 'challenge' in html.lower()[:200])

if len(html) > 10000:
    # Extract movie items
    items = driver.find_elements(By.CSS_SELECTOR, 'li.movieItem')
    print('Items found:', len(items))
    if items:
        for item in items[:3]:
            link = item.find_element(By.TAG_NAME, 'a')
            title = item.find_element(By.CSS_SELECTOR, 'h1.BottomTitle')
            img = item.find_element(By.TAG_NAME, 'img')
            cat = item.find_elements(By.CSS_SELECTOR, 'span.cat_name')
            print('  Title:', title.text[:50])
            print('  URL:', link.get_attribute('href'))
            print('  Image:', img.get_attribute('src'))
            if cat:
                print('  Category:', cat[0].text)
            print()

driver.quit()
