import requests, re

ajax_url = 'https://web.topcinemaa.com/wp-content/themes/movies2023/Ajaxat/Single/Server.php'
personhood_url = 'https://web.topcinemaa.com/%D9%81%D9%8A%D9%84%D9%85-personhood-2025-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/'
watch_url = personhood_url + 'watch/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
    'X-Requested-With': 'XMLHttpRequest',
    'Origin': 'https://web.topcinemaa.com',
}

s = requests.Session()
s.headers.update(headers)
s.get(personhood_url, timeout=30)
print('Visited main page')

r = s.get(watch_url, timeout=30)
r.encoding = 'utf-8'
html = r.text
print('Watch page status:', r.status_code)

# Find server items
server_items = re.findall(r'<li[^>]*data-id="(\d+)"[^>]*data-server="(\d+)"[^>]*>.*?<span>(.*?)</span>', html, re.DOTALL)
print('Server items:', len(server_items))
for si in server_items[:3]:
    print('  data-id={}, data-server={}, name={}'.format(si[0], si[1], si[2].strip()))

if server_items:
    post_id = server_items[0][0]
    print('Post ID:', post_id)
    
    # Try AJAX
    r2 = s.post(ajax_url, data={'id': post_id, 'i': '0'}, headers={**headers, 'Referer': watch_url}, timeout=15)
    r2.encoding = 'utf-8'
    print('AJAX response ({} chars): {}'.format(len(r2.text), r2.text[:200]))
    
    iframes = re.findall(r'<iframe[^>]+src="([^"]+)"', r2.text)
    print('Iframes:', iframes)
