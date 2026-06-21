import requests, re
headers = {'User-Agent': 'Mozilla/5.0'}

# Check multiple movies with different types
urls = [
    ('اجنبي', 'https://tuktukhd.com/%d9%81%d9%8a%d9%84%d9%85-erupcja-2026-%d9%85%d8%aa%d8%b1%d8%ac%d9%85/'),
    ('هندي', None),  # Will search for a Hindi movie
]

# Just use the same page and analyze catssection more deeply
url = 'https://tuktukhd.com/%d9%81%d9%8a%d9%84%d9%85-erupcja-2026-%d9%85%d8%aa%d8%b1%d8%ac%d9%85/'
r = requests.get(url, timeout=15, headers=headers)
html = r.content.decode('utf-8')

# Extract catssection div fully
cs = re.search(r'class="catssection"[^>]*>(.*?)</section>', html, re.DOTALL)
if not cs:
    cs = re.search(r'class="catssection"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
if not cs:
    # Find by looking for التصنيفات span
    cs = re.search(r'<span>التصنيفات</span>(.*?)</li>', html, re.DOTALL)

if cs:
    content = cs.group(1)
    print('catssection content (first 1000 chars):')
    print(content[:1000])
else:
    # Search for التصنيفات
    idx = html.find('التصنيفات')
    if idx >= 0:
        print('Found التصنيفات at position', idx)
        print(html[idx:idx+500])
    else:
        print('التصنيفات not found')

print()
print('--- Alternative: look for category links near المدة section ---')
