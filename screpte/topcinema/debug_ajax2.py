import requests, re

ajax_url = 'https://web.topcinemaa.com/wp-content/themes/movies2023/Ajaxat/Single/Server.php'
main_url = 'https://web.topcinemaa.com/%D9%81%D9%8A%D9%84%D9%85-vampires-of-the-velvet-lounge-2026-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/'
watch_url = main_url + 'watch/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': 'https://web.topcinemaa.com',
}

# First visit main page to get cookies
s = requests.Session()
s.headers.update(headers)
r = s.get(main_url, timeout=30)
print('Main page status:', r.status_code)
print('Cookies:', dict(s.cookies))

# Now try the AJAX call with proper referer
r2 = s.post(ajax_url, data={'id': '226558', 'i': '0'}, headers={**headers, 'Referer': watch_url}, timeout=30)
r2.encoding = 'utf-8'
print('AJAX response (server 0, {} chars):'.format(len(r2.text)))
print(r2.text[:500])

# Try with the main page as referer
r3 = s.post(ajax_url, data={'id': '226558', 'i': '0'}, headers={**headers, 'Referer': main_url}, timeout=30)
r3.encoding = 'utf-8'
print('\nWith main referer ({} chars):'.format(len(r3.text)))
print(r3.text[:500])

# Try server 1
r4 = s.post(ajax_url, data={'id': '226558', 'i': '1'}, headers={**headers, 'Referer': watch_url}, timeout=30)
r4.encoding = 'utf-8'
print('\nServer 1 ({} chars):'.format(len(r4.text)))
print(r4.text[:500])

# Try all servers for post 226558
for i in range(9):
    r = s.post(ajax_url, data={'id': '226558', 'i': str(i)}, headers={**headers, 'Referer': watch_url}, timeout=30)
    r.encoding = 'utf-8'
    iframes = re.findall(r'<iframe[^>]+src="([^"]+)"', r.text)
    srcs = re.findall(r'src="([^"]+)"', r.text)
    print('Server {}: {} chars, iframes={}, srcs={}'.format(i, len(r.text), len(iframes), len(srcs)))
    if iframes:
        print('  iframe: {}'.format(iframes[0]))
