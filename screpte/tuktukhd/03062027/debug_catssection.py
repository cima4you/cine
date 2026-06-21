import requests, re
headers = {'User-Agent': 'Mozilla/5.0'}

url = 'https://tuktukhd.com/%d9%81%d9%8a%d9%84%d9%85-erupcja-2026-%d9%85%d8%aa%d8%b1%d8%ac%d9%85/'
r = requests.get(url, timeout=15, headers=headers)
html = r.content.decode('utf-8')

# Find catssection content
cs = re.search(r'class="catssection"[^>]*>(.*?)</div>', html, re.DOTALL)
if cs:
    print('catssection content:')
    print(cs.group(1)[:500])
else:
    print('catssection not found')

print()

# Look for category URL patterns in the page that indicate the actual category
# e.g. category/movies-2/افلام-اجنبي/
cat_matches = re.findall(r'href="([^"]*category/movies-2/[^"]*)"', html)
print('Category URLs in page:')
for c in cat_matches:
    print('  ' + c)

print()

# Also check categories-2 URLs or similar
all_matches = re.findall(r'href="([^"]*category[^"]*)"', html)
print('All category hrefs:')
seen = set()
for c in all_matches:
    if c not in seen:
        seen.add(c)
        print('  ' + c)
