import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3'})
s.get('https://yam.ahwaktv.net/', timeout=30)

for pg in [1,2,5,6,56,57]:
    resp = s.get('https://yam.ahwaktv.net/category.php?cat=moslslat-ramdan-2023&page=' + str(pg), timeout=30)
    items = re.findall(r'watch\.php\?vid=([a-f0-9]+)"[^>]*title="([^"]*)"', resp.text)
    print('Page %d: %d items' % (pg, len(items)))
    if items:
        for v,t in items[:2]:
            print('  %s | %s' % (v, t[:60]))
