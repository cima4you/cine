import requests, re, html

headers = {'User-Agent': 'Mozilla/5.0'}
url = 'https://tuktukhd.com/category/anime-6/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d9%86%d9%85%d9%8a/page/2/'
r = requests.get(url, headers=headers, timeout=15)

items = re.findall(
    r'<a[^>]*href="(https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+)"[^>]*>.*?<img[^>]*alt="([^"]+)"[^>]*>.*?</a>',
    r.text, re.DOTALL
)

print('Total items via a>img: {}\n'.format(len(items)))

pass_count = 0
fail_count = 0
for href, alt in items:
    alt = alt.strip()
    m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم(?:\s+اون\s+لاين)?', alt)
    if m:
        pass_count += 1
    else:
        fail_count += 1
        print('  FAIL: {}'.format(alt[:80]))
        
print('\nPassed: {}, Failed: {}'.format(pass_count, fail_count))
