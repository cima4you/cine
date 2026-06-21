from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re, time

options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
options.add_argument('--lang=ar')
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument('--disable-blink-features=AutomationControlled')

driver = webdriver.Chrome(options=options)

# Execute CDP commands to hide webdriver
driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': '''
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
    '''
})

driver.get('https://cimafre.site/')
time.sleep(3)

driver.get('https://cimafre.site/watch.php?vid=19997b01f')

# Wait up to 15 seconds for WatchList to appear
try:
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '.WatchList li'))
    )
    print('WatchList found via wait!')
except:
    print('WatchList not found via wait')

time.sleep(3)

html = driver.page_source
print(f'HTML size: {len(html)} bytes')

m = re.search(r'<ul[^>]*class="[^"]*WatchList[^"]*"[^>]*>.*?</ul>', html, re.DOTALL)
if m:
    print('\nWatchList FOUND!')
    print(m.group(0))
else:
    print('\nWatchList NOT FOUND')

# Check via JS
wl = driver.execute_script("return document.querySelector('.WatchList') ? document.querySelector('.WatchList').outerHTML : 'NONE'")
print(f'\nWatchList via JS: {wl[:1000]}')

# Check if any AJAX requests were made
perf_logs = []
try:
    perf_logs = driver.get_log('performance')
except:
    pass

ajax_urls = set()
for log in perf_logs:
    try:
        import json
        msg = json.loads(log['message'])
        if msg.get('message', {}).get('method', '') == 'Network.requestWillBeSent':
            url = msg['message']['params']['request']['url']
            if any(k in url for k in ['ajax', 'api', 'source', 'server', 'embed', 'watch']):
                ajax_urls.add(url)
    except:
        pass

if ajax_urls:
    print(f'\nRelevant network requests ({len(ajax_urls)}):')
    for u in sorted(ajax_urls):
        print(f'  {u}')

with open('screpte/cimafre/data/selenium_final.html', 'w', encoding='utf-8') as f:
    f.write(html)

driver.quit()
print('\nDone!')
