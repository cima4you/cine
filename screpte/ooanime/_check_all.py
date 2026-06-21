import requests, re, json

def get_page(url):
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    r.encoding = 'utf-8'
    return r.text

# Check cartoon page for pagination
t = get_page('https://www.ooanime.com/cartoon')

# Look for all page numbers/links
pages = re.findall(r'\?page=(\d+)', t)
print(f'Page numbers found: {pages[:20]}')

# Look for pagination container
pagi = re.findall(r'<ul class="[^"]*pagination[^"]*"[^>]*>(.*?)</ul>', t, re.DOTALL)
print(f'Pagination containers: {len(pagi)}')
for p in pagi[:3]:
    links = re.findall(r'href="([^"]+)"', p)
    print(f'  Links: {links}')

# Also check for "next" in any context
next = re.findall(r'>(التالي|التالي<|<)', t)
print(f'Next text: {next[:5]}')

# Check how many series (from different folders)
series = re.findall(r'/series/(\d+)/', t)
unique_series = sorted(set(series))
print(f'Series IDs: {unique_series}')
print(f'Count: {len(unique_series)}')

# Check if there are other cartoon pages
t2 = get_page('https://www.ooanime.com/cartoon?page=2')
series2 = re.findall(r'/series/(\d+)/', t2)
unique_series2 = sorted(set(series2))
print(f'\nPage 2 series: {unique_series2}')
print(f'Page 2 count: {len(unique_series2)}')
print(f'Page 2 length: {len(t2)}')
print(f'Page 2 has content: {len(series2) > 0}')
