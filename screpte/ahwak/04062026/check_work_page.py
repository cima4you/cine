import requests, re, sys, time
sys.stdout.reconfigure(encoding='utf-8')
s = requests.Session()
s.headers.update({'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'en-US,en;q=0.5'})
s.get('https://www.elcinema.com/')

# Check the actual work page for توبة (work/2072893) to see what image URL is actually used in the HTML
r = s.get('https://www.elcinema.com/work/2072893/', timeout=15)
print('Page loaded: %d' % r.status_code)

# Find ALL image URLs on the page with 'uploads'
imgs = re.findall(r'<img[^>]*src="([^"]*media[^"]*\.com[^"]*)"', r.text)
for img in imgs[:20]:
    print('  IMG: %s' % img[:120])

# Also look for the main poster specifically
# The poster is usually in a specific container
pm = re.search(r'poster.*?src="([^"]*)"', r.text, re.IGNORECASE | re.DOTALL)
if pm:
    print('POSTER match: %s' % pm.group(1)[:120])

# Check og:image meta tag
ogm = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]*)"', r.text)
if ogm:
    print('og:image: %s' % ogm.group(1)[:120])

# Try the _150x200 size variants that appeared in earlier test
# The page for أمينة حاف 2 had multiple sizes
for m in re.finditer(r'src="(https://[^"]*?/uploads/[^"]*?\d+x\d+[^"]*?)"', r.text):
    print('  Sized: %s' % m.group(1)[:120])
