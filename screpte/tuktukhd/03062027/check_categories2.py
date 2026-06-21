import requests, re
r = requests.get('https://tuktukhd.com/category/movies-2/', headers={'User-Agent':'Mozilla/5.0'}, timeout=15)
text = r.content.decode('utf-8')

# Get full hrefs
hrefs = re.findall(r'href="(https://tuktukhd\.com/category/movies-2/[^"]*)"', text)
names = re.findall(r'>([^<]+)</a>', text)

# Filter subcategories
seen = set()
for href in hrefs:
    # Decode URL to show full path
    from urllib.parse import unquote
    decoded = unquote(href)
    # Only keep subcategory URLs (not the main /movies-2/ itself)
    if href.rstrip('/') != 'https://tuktukhd.com/category/movies-2':
        if href not in seen:
            seen.add(href)
            print(decoded[:80])
            print(f'  -> {href}')
