import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time, os, shutil

cache_dir = os.path.expanduser('~/.undetected_chromedriver')
if os.path.exists(cache_dir):
    shutil.rmtree(cache_dir)

# Try without headless
driver = uc.Chrome(headless=False, version_main=148)
driver.get('https://tv8.egydead.live/')
print('Waiting...')

for i in range(60):
    time.sleep(1)
    title = driver.title
    html = driver.page_source
    is_challenge = 'Un instant' in title or 'Just a moment' in title
    if not is_challenge:
        print('Solved after {}s'.format(i + 1))
        break
    if i % 5 == 0:
        print('  waiting... ({}) title={}'.format(i + 1, title))

html = driver.page_source
print('Length:', len(html))
print('Title:', driver.title)

if 'Un instant' not in html:
    items = driver.find_elements(By.CSS_SELECTOR, 'li.movieItem')
    print('li.movieItem:', len(items))
    if items:
        for item in items[:2]:
            print(item.get_attribute('outerHTML')[:300])
    else:
        # Save HTML for analysis
        with open('egydead_real.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print('Saved to egydead_real.html')

input('Press Enter to exit...')
driver.quit()
