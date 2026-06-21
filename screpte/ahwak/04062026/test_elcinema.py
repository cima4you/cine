import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US,en;q=0.5'})
s.get('https://www.elcinema.com/')
s.headers.update({'Referer': 'https://www.elcinema.com/'})

title = 'أمينة حاف 2'
r = s.get('https://www.elcinema.com/search/', params={'q': title}, timeout=15)
match = re.search(r'href="(/work/\d+/)"', r.text)
if match:
    href = match.group(1)
    print('Work page: https://www.elcinema.com' + href)
    r2 = s.get('https://www.elcinema.com' + href, timeout=15)
    imgs = re.findall(r'<img[^>]*src="([^"]*)"', r2.text)
    for img in imgs:
        if 'uploads' in img or 'poster' in img.lower():
            print('  Image: ' + img[:120])
    # Try different sizes
    for m in re.finditer(r'src="(.*?uploads.*?)"', r2.text):
        print('  Upload: ' + m.group(1))
else:
    print('No results found')
