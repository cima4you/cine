import requests, re

ajax_url = 'https://web.topcinemaa.com/wp-content/themes/movies2023/Ajaxat/Single/Server.php'
personhood_url = 'https://web.topcinemaa.com/%D9%81%D9%8A%D9%84%D9%85-personhood-2025-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/'
watch_url = personhood_url + 'watch/'

# Same headers as the main script's HEADERS
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

# Visit watch page
r = ses.get(watch_url, timeout=30)
print('Watch page status:', r.status_code)

# Now try AJAX WITHOUT specific AJAX headers
r2 = ses.post(ajax_url, data={'id': '226575', 'i': '0'}, timeout=15)
r2.encoding = 'utf-8'
print('AJAX (no special headers) response: {} chars'.format(len(r2.text)))
print(repr(r2.text[:200]))

iframes = re.findall(r'<iframe[^>]+src="([^"]+)"', r2.text)
print('Iframes:', iframes)
