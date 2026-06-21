import requests, re, base64
headers = {'User-Agent': 'Mozilla/5.0'}

url = 'https://tuktukhd.com/%d9%81%d9%8a%d9%84%d9%85-erupcja-2026-%d9%85%d8%aa%d8%b1%d8%ac%d9%85/'
r = requests.get(url, timeout=20, headers=headers)
html = r.content.decode('utf-8')

print('Length:', len(html))

# Check watch URLs
crypts = re.findall(r'data-crypt="([^"]+)"', html)
print('data-crypt found:', len(crypts))
watch_urls = []
for c in crypts:
    try:
        wu = base64.b64decode(c).decode('utf-8')
        watch_urls.append(wu)
    except:
        pass
print('Decoded watch URLs:', len(watch_urls))

# Check server items
si = re.findall(r'<li[^>]*class="[^"]*server--item[^"]*"[^>]*>.*?<span>([^<]*)</span>', html, re.DOTALL)
print('Server items:', len(si))

# Check classify
cs = re.search(r'class="catssection"[^>]*>(.*?)</section>', html, re.DOTALL)
if cs:
    print('catssection found')
    cat_links = re.findall(r'<a[^>]*href="([^"]*category[^"]*)"[^>]*>([^<]+)</a>', cs.group(1))
    print('Category links:', len(cat_links))
    for href, label in cat_links:
        print('  {} -> {}'.format(label, href))
else:
    print('catssection NOT found')

# Check seasons/episodes detection
if re.search(r'class="[^"]*seasons[^"]*"', html):
    print('Has seasons class - would be skipped')
if re.search(r'class="[^"]*episodes[^"]*"', html):
    print('Has episodes class - would be skipped')
