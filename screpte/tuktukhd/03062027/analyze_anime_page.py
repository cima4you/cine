import re

with open('scripts/tuktukhd/anime_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

alts = re.findall(r'alt="([^"]+)"', html)
print('=== ALT texts (first 30) ===')
for a in alts[:30]:
    print(repr(a))

film_urls = re.findall(r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+', html)
print('\n=== Film URLs (first 10) ===')
for u in film_urls[:10]:
    print(u)

cat_urls = re.findall(r'https://tuktukhd\.com/category/anime[^"]*', html)
print('\n=== Category URLs ===')
for u in cat_urls[:3]:
    print(u)

# Check pagination
pages = re.findall(r'page/(\d+)/', html)
print('\n=== Pages found ===')
print(sorted(set(int(p) for p in pages)))
