import requests, re

BASE = 'https://cimafre.site'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

r = requests.get(BASE + '/category.php?cat=arabic-moives&page=1&order=DESC', headers=HEADERS, timeout=20)
r.encoding = 'utf-8'
t = r.text

# Pagination links
pages = re.findall(r'href="([^"]*page=(\d+)[^"]*)"', t)
page_nums = sorted(set(int(p[1]) for p in pages))
print(f'Page links: {len(pages)}')
print(f'Pages: {page_nums[:15]}...' if len(page_nums) > 15 else f'Pages: {page_nums}')
print(f'Max page: {max(page_nums)}' if page_nums else 'No pages')

# Check next/prev
next_prev = re.findall(r'(next|السابق|التالي|Previous)', t, re.IGNORECASE)
print(f'Navigation: {len(next_prev)}')

# Find the last page link
last_pages = re.findall(r'href="([^"]*page=(\d+)[^"]*)"[^>]*>\s*(\d+)\s*<', t)
for href, num, text in last_pages[:5]:
    print(f'  page={num} -> text="{text}"')

# Now visit a detail page
r2 = requests.get(f'{BASE}/watch.php?vid=19997b01f', headers=HEADERS, timeout=20)
r2.encoding = 'utf-8'
t2 = r2.text

with open('screpte/cimafre/data/detail.html', 'w', encoding='utf-8') as f:
    f.write(t2)
print(f'\nDetail saved ({len(t2)} bytes)')

title_m = re.search(r'<title>(.*?)</title>', t2)
if title_m: print(f'Title: {title_m.group(1)[:80]}')

watch = re.findall(r'data-embed-url="([^"]+)"', t2)
print(f'Watch servers: {len(watch)}')

download = re.findall(r'data-download-url="([^"]+)"', t2)
print(f'Download servers: {len(download)}')

# Description
desc = re.search(r'<p>(.*?)</p>', t2, re.DOTALL)
if desc:
    d = re.sub(r'<[^>]+>', '', desc.group(1))[:200]
    print(f'Description: {d}')
