import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3'})
s.get('https://yam.ahwaktv.net/', timeout=30)

resp = s.get('https://yam.ahwaktv.net/category.php?cat=moslslat-ramdan-2023&page=56', timeout=30)
resp2 = s.get('https://yam.ahwaktv.net/category.php?cat=moslslat-ramdan-2023&page=57', timeout=30)

# Check if page 58 exists
resp3 = s.get('https://yam.ahwaktv.net/category.php?cat=moslslat-ramdan-2023&page=58', timeout=30)
items58 = re.findall(r'watch\.php\?vid=([a-f0-9]+)"[^>]*title="([^"]*)"', resp3.text)
print('Page 58 items: %d' % len(items58))

items57 = re.findall(r'watch\.php\?vid=([a-f0-9]+)"[^>]*title="([^"]*)"', resp2.text)
print('Page 57 items: %d' % len(items57))

# Check pagination HTML on page 56
pag = re.search(r'class="pagination[^"]*"[^>]*>(.*?)</ul>', resp.text, re.DOTALL)
if pag:
    print('Pagination HTML (page 56): %s' % pag.group(1)[:500])

# Search for page links in the text
pags = re.findall(r'page=\d+', resp.text)
print('Page links on 56: %s' % sorted(set(pags)))
pags57 = re.findall(r'page=\d+', resp2.text)
print('Page links on 57: %s' % sorted(set(pags57)))
