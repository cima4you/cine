import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time, os, shirt, ctypes

# Hide console window
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

cache_dir = os.path.expanduser('~/.undetected_chromedriver')
if os.path.exists(cache_dir):
    shutil.rmtree(cache_dir)

# Run with hidden window but NOT headless (Cloudflare blocks headless)
options = uc.ChromeOptions()
options.add_argument('--window-position=-32000,-32000')  # Move off-screen
options.add_argument('--window-size=1,1')  # Tiny window
driver = uc.Chrome(headless=False, version_main=148, options=options)

driver.get('https://tv8.egydead.live/')
for i in range(30):
    time.sleep(1)
    title = driver.title
    if 'Un instant' not in title and 'Just a moment' not in title:
        print('Solved after {}s'.format(i + 1))
        break
else:
    print('Timeout')

html = driver.page_source
print('Length:', len(html))
items = driver.find_elements(By.CSS_SELECTOR, 'li.movieItem')
print('Items:', len(items))

if items:
    # Test detail page
    driver.get('https://tv8.egydead.live/sinners-2025-1080p-bluray/')
    time.sleep(3)
    detail_html = driver.page_source
    print('\nDetail page length:', len(detail_html))
    
    # Look for server/player data
    import re
    for keyword in ['data-crypt', 'data-real-url', 'iframe', 'server', 'player']:
        matches = re.findall(keyword, detail_html)
        print('  {}: {}'.format(keyword, len(matches)))

driver.quit()
