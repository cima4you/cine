import re

with open('scripts/tuktukhd/anime_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find <a> tags containing <img> with film alt text
items = re.findall(
    r'<a[^>]*href="(https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+)"[^>]*>.*?<img[^>]*alt="(\u0641\u064A\u0644\u0645[^"]+)"[^>]*>.*?</a>',
    html, re.DOTALL
)
print('Found {} items via <a><img> pattern'.format(len(items)))
for href, alt in items[:5]:
    print('  alt={}'.format(alt[:70]))
    print('  href={}'.format(href[:70]))

# Alternative: find <li> items
lis = re.findall(r'<li[^>]*class="[^"]*poster[^"]*"[^>]*>.*?</li>', html, re.DOTALL)
print('\nPoster <li> items:', len(lis))
for li in lis[:2]:
    a = re.search(r'href="([^"]+)"', li)
    img = re.search(r'alt="([^"]+)"', li)
    print('  href={} alt={}'.format(a.group(1)[:60] if a else 'N/A', img.group(1)[:60] if img else 'N/A'))
