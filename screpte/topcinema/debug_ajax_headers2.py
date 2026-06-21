import requests, re

ajax_url = 'https://web.topcinemaa.com/wp-content/themes/movies2023/Ajaxat/Single/Server.php'
personhood_url = 'https://web.topcinemaa.com/%D9%81%D9%8A%D9%84%D9%85-personhood-2025-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/'
watch_url = personhood_url + 'watch/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
    'Referer': 'https://web.topcinemaa.com/',
}

ses = requests.Session()
ses.headers.update(headers)

# Visit main page
ses.get(personhood_url, timeout=30)
print('Visited main page')

r = ses.get(watch_url, timeout=30)

# Test 1: Only X-Requested-With
r1 = ses.post(ajax_url, data={'id': '226575', 'i': '0'},
              headers={'X-Requested-With': 'XMLHttpRequest'}, timeout=15)
r1.encoding = 'utf-8'
print('Test 1 (X-Requested-With only): {} chars, iframes={}'.format(
    len(r1.text), bool(re.search(r'<iframe', r1.text))))

# Test 2: X-Requested-With + Content-Type
r2 = ses.post(ajax_url, data={'id': '226575', 'i': '0'},
              headers={'X-Requested-With': 'XMLHttpRequest',
                       'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}, timeout=15)
r2.encoding = 'utf-8'
print('Test 2 (both): {} chars, iframes={}'.format(
    len(r2.text), bool(re.search(r'<iframe', r2.text))))

# Test 3: Content-Type only
r3 = ses.post(ajax_url, data={'id': '226575', 'i': '0'},
              headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}, timeout=15)
r3.encoding = 'utf-8'
print('Test 3 (Content-Type only): {} chars, iframes={}'.format(
    len(r3.text), bool(re.search(r'<iframe', r3.text))))

# Test 4: X-Requested-With + Referer
r4 = ses.post(ajax_url, data={'id': '226575', 'i': '0'},
              headers={'X-Requested-With': 'XMLHttpRequest',
                       'Referer': watch_url}, timeout=15)
r4.encoding = 'utf-8'
print('Test 4 (X-Requested-With + Referer): {} chars, iframes={}'.format(
    len(r4.text), bool(re.search(r'<iframe', r4.text))))

# Test 5: All + Accept: */*
r5 = ses.post(ajax_url, data={'id': '226575', 'i': '0'},
              headers={'X-Requested-With': 'XMLHttpRequest',
                       'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                       'Accept': '*/*',
                       'Referer': watch_url}, timeout=15)
r5.encoding = 'utf-8'
print('Test 5 (all): {} chars, iframes={}'.format(
    len(r5.text), bool(re.search(r'<iframe', r5.text))))
