from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import json, time, re

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

driver = webdriver.Chrome(options=options)
driver.get('https://cimafre.site/watch.php?vid=19997b01f')

# Wait longer
time.sleep(10)

# Get performance logs
logs = driver.get_log('performance')
print(f'Network logs: {len(logs)}')

# Look for XHR/fetch requests with data
urls = set()
for log in logs:
    try:
        msg = json.loads(log['message'])
        if 'Network.response' in msg.get('method', ''):
            params = msg.get('params', {})
            req = params.get('request', {})
            url = req.get('url', '')
            if 'ajax' in url or 'api' in url or 'source' in url or 'embed' in url or 'server' in url:
                urls.add(url)
                print(f'  Request: {url}')
            if '.m3u8' in url or '.mp4' in url:
                urls.add(url)
                print(f'  MEDIA: {url}')
    except:
        pass

# Also try direct JS evaluation
watchlist_js = driver.execute_script("""
    // Check for any global variables with server data
    const keys = Object.keys(window);
    const results = [];
    for (const k of keys) {
        if (k.toLowerCase().includes('server') || k.toLowerCase().includes('source') || k.toLowerCase().includes('embed')) {
            results.push({key: k, val: JSON.stringify(window[k]).substring(0, 200)});
        }
    }
    // Also check the WatchList element existence
    const wl = document.querySelector('.WatchList');
    results.push({key: 'WatchList element', val: wl ? wl.innerHTML.substring(0, 500) : 'null'});
    return results;
""")

print('\nJS globals and WatchList:')
for r in watchlist_js:
    print(f'  {r["key"]}: {r["val"]}')

# Try getting the full HTML and save
html = driver.page_source
with open('screpte/cimafre/data/selenium_wait10s.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\nSaved: {len(html)} bytes')
print(f'WatchList in HTML: {"WatchList" in html}')
print(f'UL.WatchList in HTML: {bool(re.search(r"<ul[^>]*WatchList", html))}')

driver.quit()
