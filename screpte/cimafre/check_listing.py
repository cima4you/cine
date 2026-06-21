import requests, re

BASE = 'https://cimafre.site'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

r = requests.get(BASE + '/category.php?cat=arabic-moives&page=1&order=DESC', headers=HEADERS, timeout=20)
r.encoding = 'utf-8'
t = r.text

# Save html to inspect
with open('screpte/cimafre/data/listing.html', 'w', encoding='utf-8') as f:
    f.write(t)
print(f'Saved listing.html ({len(t)} bytes)')

# Find all watch.php links
watch_links = re.findall(r'href="([^"]*watch\.php[^"]*)"', t)
print(f'watch.php links: {len(watch_links)}')
for l in watch_links[:5]:
    print(f'  {l}')

# Find all movie-like sections
sections = re.findall(r'<div[^>]*class="[^"]*movie[^"]*"[^>]*>', t, re.DOTALL)
print(f'\nmovie class divs: {len(sections)}')

# Find thumbnails / posters
thumbs = re.findall(r'src="([^"]*uploads/thumbs[^"]+)"', t)
print(f'\nThumbnails: {len(thumbs)}')
for th in thumbs[:3]:
    print(f'  {th}')

# Find alt text of movies
alts = re.findall(r'alt="([^"]*فيلم[^"]*)"', t)
print(f'\nMovie alt texts: {len(alts)}')
for a in alts[:3]:
    print(f'  {a[:80]}')
