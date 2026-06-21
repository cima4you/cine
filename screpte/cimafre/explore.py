import requests, re, json

BASE = 'https://cimafre.site'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# Explore the arabic movies listing page
r = requests.get(BASE + '/category.php?cat=arabic-moives', headers=HEADERS, timeout=20)
r.encoding = 'utf-8'
t = r.text

print(f'Status: {r.status_code}, Length: {len(t)}')

# Find movie links (detail pages)
movies = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*alt="([^"]*)"', t, re.DOTALL)
print(f'\nMovies found (img links): {len(movies)}')
for url, poster, alt in movies[:3]:
    print(f'  URL: {url}')
    print(f'  Poster: {poster[:60]}')
    print(f'  Alt: {alt[:60]}')

# Find all links that look like movie detail pages
movie_links = re.findall(r'<a\s+href="([^"]+)"[^>]*>\s*<img[^>]*src="[^"]*"[^>]*>', t)
print(f'\nMovie links: {len(movie_links)}')
for link in movie_links[:5]:
    print(f'  {link}')

# Find pagination
pages = re.findall(r'href="([^"]*page[^"]*)"', t)
if not pages:
    pages = re.findall(r'href="([^"]*\d+[^"]*)"', t)
print(f'\nPage links: {len(pages)}')
for p in pages[:10]:
    print(f'  {p}')

# Find Next page
next_pages = re.findall(r'next|التالي|صفحة.*تالية|last|Page', t, re.IGNORECASE)
print(f'\nNavigation keywords: {len(next_pages)}')

# Check for category navigation
cats = re.findall(r'category\.php\?cat=([^"&\s]+)', t)
print(f'\nCategories: {len(set(cats))}')
print(set(cats))
