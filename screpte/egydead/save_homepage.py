import undetected_chromedriver as uc
import time, os, shutil

cache_dir = os.path.expanduser('~/.undetected_chromedriver')
if os.path.exists(cache_dir):
    shutil.rmtree(cache_dir)

driver = uc.Chrome(headless=True, version_main=148)
driver.get('https://tv8.egydead.live/')
time.sleep(5)

html = driver.page_source
with open('egydead_debug.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Saved: {} bytes'.format(len(html)))
driver.quit()
