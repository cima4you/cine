import requests, sys, re
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://tv8.egydead.live/wp-content/uploads/2024/06/%D9%81%D9%8A%D9%84%D9%85-%D8%A8%D8%A7%D9%83%D9%8A-%D9%87%D8%A7%D9%86%D9%85%D8%A7-%D8%B6%D8%AF-%D9%83%D9%8A%D9%86%D8%BA%D8%A7%D9%86-%D8%A7%D8%B4%D9%88%D8%B1%D8%A7-2024-%D9%85%D8%AF%D8%A8%D9%84%D8%AC.jpg'

# Try with a proper browser session
s = requests.Session()
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Sec-Fetch-Dest': 'image',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'cross-site',
})

# First visit the home page to get cookies
r0 = s.get('https://tv8.egydead.live/', timeout=15)
print('Homepage: Status=%d, Cookies=%s' % (r0.status_code, dict(s.cookies)))

# Now try the image with cookies
r = s.get(url, timeout=15)
print('Image with cookies: Status=%d, Length=%d, Content-Type=%s' % (r.status_code, len(r.content), r.headers.get('Content-Type','')))

if r.status_code == 403:
    # Check what the error page says
    print('Response snippet:', r.text[:500])
    # Check for any specific headers
    for k, v in r.headers.items():
        print('  Header: %s: %s' % (k, v))
