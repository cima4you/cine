import undetected_chromedriver as uc
import requests, json, time, os, shutil, re, sys

sys.stdout.reconfigure(encoding='utf-8')

cache = os.path.expanduser('~/.undetected_chromedriver')
if os.path.exists(cache): shutil.rmtree(cache)

driver = uc.Chrome(headless=False, version_main=148)
driver.get('https://tv8.egydead.live/sinners-2025-1080p-bluray/')
for i in range(30):
    time.sleep(1)
    if 'Un instant' not in driver.title:
        print('Solved after {}s'.format(i+1))
        break

selenium_cookies = driver.get_cookies()
print('Cookies:', len(selenium_cookies))
ua = driver.execute_script('return navigator.userAgent')
print('UA:', ua[:80])

s = requests.Session()
s.headers.update({'User-Agent': ua})
for c in selenium_cookies:
    s.cookies.set(c['name'], c['value'], domain=c.get('domain', ''))

r = s.get('https://tv8.egydead.live/sinners-2025-1080p-bluray/', timeout=15)
print('GET status:', r.status_code, 'len:', len(r.text))
print('Has challenge:', 'Just a moment' in r.text or 'challenge' in r.text)
print('Has serversList:', 'serversList' in r.text)

s.headers.update({'Content-Type': 'application/x-www-form-urlencoded'})
r2 = s.post('https://tv8.egydead.live/sinners-2025-1080p-bluray/', data={'View': '1'}, timeout=15)
print('POST status:', r2.status_code, 'len:', len(r2.text))
print('Has challenge:', 'Just a moment' in r2.text or 'challenge' in r2.text)
print('Has serversList:', 'serversList' in r2.text)
print('Has data-link:', 'data-link' in r2.text)

if 'data-link' in r2.text:
    links = re.findall(r'data-link="([^"]+)"', r2.text)
    print('data-link count:', len(links))
    for l in links[:5]:
        print(' ', l[:100])
else:
    with open('egydead_post_result.html', 'w', encoding='utf-8') as f:
        f.write(r2.text)
    print('Saved POST response to egydead_post_result.html')

driver.quit()
