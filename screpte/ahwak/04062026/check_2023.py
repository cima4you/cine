import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3'})
resp = s.get('https://yam.ahwaktv.net/', timeout=30)
resp2 = s.get('https://yam.ahwaktv.net/category.php?cat=moslslat-ramdan-2023', timeout=30)
print('Status: %d' % resp2.status_code)
pages = re.findall(r'page=(\d+)', resp2.text)
if pages:
    print('Found pages: %s' % sorted(set(pages), key=int))
    print('Max page: %s' % max(set(pages), key=int))
items = re.findall(r'watch\.php\?vid=([a-f0-9]+)"[^>]*title="([^"]*)"', resp2.text)
print('Items on page 1: %d' % len(items))
if items:
    for v,t in items[:3]:
        print('  %s | %s' % (v, t[:60]))
