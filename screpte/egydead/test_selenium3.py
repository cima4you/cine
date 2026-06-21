import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, os, shutil

cache_dir = os.path.expanduser('~/.undetected_chromedriver')
if os.path.exists(cache_dir):
    shutil.rmtree(cache_dir)

options = uc.ChromeOptions()
options.add_argument('--disable-blink-features=AutomationControlled')
driver = uc.Chrome(headless=False, version_main=148, options=options)
driver.get('https://tv8.egydead.live/')
print('Waiting for page...')

# Wait up to 30 seconds for the page to fully load (Cloudflare challenge to solve)
try:
    WebDriverWait(driver, 30).until(
        lambda d: 'Just a moment' not in d.title and 'Un instant' not in d.title
    )
    print('Challenge passed!')
except:
    print('Timeout waiting, current title:', driver.title)

time.sleep(3)
html = driver.page_source
print('Page length:', len(html))
print('Title:', driver.title)
print('Is challenge:', 'Just a moment' in html or 'Un instant' in html or 'challenge' in html.lower()[:500])

if len(html) > 20000 and 'Un instant' not in html:
    items = driver.find_elements(By.CSS_SELECTOR, 'li.movieItem')
    print('Items found by class:', len(items))
    
    # Try to find any movie-like elements
    for sel in ['li.movieItem', 'div.post', 'article', '.movie', '.post', '.item', '[class*="movie"]', '[class*="post"]']:
        elements = driver.find_elements(By.CSS_SELECTOR, sel)
        if elements:
            print('  {}: {} elements'.format(sel, len(elements)))
    
    # Check the main content sections
    for tag in ['h1', 'h2', 'h3', 'a']:
        elements = driver.find_elements(By.TAG_NAME, tag)
        texts = [e.text[:50] for e in elements[:10] if e.text.strip()]
        if texts:
            print('  <{}> texts: {}'.format(tag, texts[:5]))

input('Press Enter to close...')
driver.quit()
