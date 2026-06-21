import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time, os, shutil

cache_dir = os.path.expanduser('~/.undetected_chromedriver')
if os.path.exists(cache_dir):
    shutil.rmtree(cache_dir)

driver = uc.Chrome(headless=True, version_main=148)
driver.get('https://tv8.egydead.live/')
print('Waiting for Cloudflare challenge...')

# Wait up to 40 seconds for challenge to resolve
for i in range(40):
    time.sleep(1)
    title = driver.title
    html = driver.page_source
    is_challenge = 'Just a moment' in title or 'Un instant' in title or 'challenge' in html.lower()[:1000]
    if not is_challenge:
        print('Challenge solved after {}s'.format(i + 1))
        break
    if i % 5 == 0:
        print('  still waiting... ({})'.format(i + 1))

html = driver.page_source
print('Final length:', len(html))
print('Title:', driver.title)
print('Is challenge:', 'Just a moment' in html or 'Un instant' in html or 'challenge' in html.lower()[:1000])

if not is_challenge and len(html) > 20000:
    items = driver.find_elements(By.CSS_SELECTOR, 'li.movieItem')
    print('li.movieItem:', len(items))
    # Try other selectors
    for sel in ['[class*="movie"]', '[class*="post"]', '[class*="item"]', 'article']:
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        if els:
            print('  {}: {}'.format(sel, len(els)))
            if els:
                print('  First:', els[0].get_attribute('outerHTML')[:300])

driver.quit()
