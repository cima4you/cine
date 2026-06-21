import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import re, time, os, shutil

cache_dir = os.path.expanduser('~/.undetected_chromedriver')
if os.path.exists(cache_dir):
    shutil.rmtree(cache_dir)

driver = uc.Chrome(headless=True, version_main=148)
driver.get('https://tv8.egydead.live/')
time.sleep(3)

html = driver.page_source
print('Page length:', len(html))
print()

# Show all class names that have "movie" or "post" or "item"
for pat in [r'class="[^"]*movie[^"]*"', r'class="[^"]*post[^"]*"', r'class="[^"]*item[^"]*"', r'class="[^"]*Item[^"]*"']:
    matches = re.findall(pat, html)
    if matches:
        print('{}: {} matches'.format(pat, len(matches)))
        for m in matches[:5]:
            print('  ', m)

print()
# Show all movie-related class names
for cls in ['movieItem', 'MovieItem', 'movie-item', 'postItem', 'BlogItem', 'videoItem']:
    items = driver.find_elements(By.CLASS_NAME, cls)
    if items:
        print('Class "{}": {} items'.format(cls, len(items)))

# Try by tag
for tag in ['li', 'div', 'article']:
    items = driver.find_elements(By.TAG_NAME, tag)
    # Check which ones have links
    count = 0
    for item in items:
        links = item.find_elements(By.TAG_NAME, 'a')
        imgs = item.find_elements(By.TAG_NAME, 'img')
        if links and imgs:
            count += 1
    if count > 1:
        print('Tag {} with a+img: {}'.format(tag, count))

driver.quit()
