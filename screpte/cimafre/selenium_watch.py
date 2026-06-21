from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re, time

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
options.add_argument('--lang=ar')

driver = webdriver.Chrome(options=options)
driver.get('https://cimafre.site/watch.php?vid=19997b01f')
time.sleep(5)
html = driver.page_source
driver.quit()

print(f'HTML size: {len(html)} bytes')

m = re.search(r'<ul[^>]*class="[^"]*WatchList[^"]*"[^>]*>.*?</ul>', html, re.DOTALL)
if m:
    print('\nWatchList FOUND!')
    print(m.group(0))
else:
    print('\nWatchList NOT FOUND')

m2 = re.search(r'<ul[^>]*class="[^"]*DownloadList[^"]*"[^>]*>.*?</ul>', html, re.DOTALL)
if m2:
    print('\nDownloadList FOUND!')
    print(m2.group(0)[:1000])
else:
    print('\nDownloadList NOT FOUND')

with open('screpte/cimafre/data/selenium_detail.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('\nSaved!')
