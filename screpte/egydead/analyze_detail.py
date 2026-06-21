import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time, os, shutil, re

cache_dir = os.path.expanduser('~/.undetected_chromedriver')
if os.path.exists(cache_dir):
    shutil.rmtree(cache_dir)

driver = uc.Chrome(headless=False, version_main=148)
driver.get('https://tv8.egydead.live/')
for i in range(30):
    time.sleep(1)
    if 'Un instant' not in driver.title and 'Just a moment' not in driver.title:
        print('Solved after {}s'.format(i + 1))
        break
print('Home loaded:', len(driver.page_source))

# Go to a movie detail page
driver.get('https://tv8.egydead.live/sinners-2025-1080p-bluray/')
time.sleep(5)
html = driver.page_source
print('Detail loaded:', len(html))

# Save detail html for analysis
with open('egydead_detail.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Saved detail to egydead_detail.html')

# Look for all key patterns
for pat in ['data-crypt', 'data-real-url', 'iframe', 'data-src', 'data-url', 'data-video', 'data-link']:
    count = len(re.findall(pat, html))
    if count:
        print('  {}: {}'.format(pat, count))

# Find server/player sections
for pat in [r'class="[^"]*server[^"]*"', r'class="[^"]*player[^"]*"', r'class="[^"]*watch[^"]*"', r'class="[^"]*download[^"]*"']:
    matches = re.findall(pat, html)
    if matches:
        print('  {}: {}'.format(pat, len(matches)))
        for m in matches[:3]:
            print('    ', m[:80])

# Check for iframes with video
iframes = driver.find_elements(By.TAG_NAME, 'iframe')
print('iframes:', len(iframes))
for iframe in iframes[:5]:
    src = iframe.get_attribute('src')
    if src:
        print('  iframe src:', src[:100])

# Check for video tags
videos = driver.find_elements(By.TAG_NAME, 'video')
print('videos:', len(videos))
sources = driver.find_elements(By.TAG_NAME, 'source')
print('sources:', len(sources))

driver.quit()
