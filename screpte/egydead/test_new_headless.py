import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time, os, shutil

cache_dir = os.path.expanduser('~/.undetected_chromedriver')
if os.path.exists(cache_dir):
    shutil.rmtree(cache_dir)

# Try new headless mode (less detectable)
options = uc.ChromeOptions()
options.add_argument('--headless=new')
options.add_argument('--window-size=1920,1080')
driver = uc.Chrome(headless=False, version_main=148, options=options)
driver.get('https://tv8.egydead.live/')
print('Waiting...')

for i in range(30):
    time.sleep(1)
    title = driver.title
    is_challenge = 'Un instant' in title or 'Just a moment' in title
    if not is_challenge:
        print('Solved after {}s'.format(i + 1))
        break
    if i % 5 == 0:
        print('  waiting... ({})'.format(i + 1))

html = driver.page_source
print('Length:', len(html))
print('Title:', driver.title)

if 'Un instant' not in html:
    items = driver.find_elements(By.CSS_SELECTOR, 'li.movieItem')
    print('li.movieItem:', len(items))

driver.quit()
