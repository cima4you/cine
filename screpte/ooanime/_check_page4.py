import re, json

with open('page.html', 'r', encoding='utf-8') as f:
    t = f.read()

# Find all series links in the page
series = re.findall(r'href="(https?://www\.ooanime\.com/series/\d+/[^"]+)"', t)
imgs = re.findall(r'<img[^>]*src="(https?://www\.ooanime\.com/files/[^"]+)"[^>]*>', t)

print(f'Series links: {len(series)}')
unique_series = list(dict.fromkeys(series))
print(f'Unique series: {len(unique_series)}')
for s in unique_series[:20]:
    print(f'  {s}')

print(f'\nImages: {len(imgs)}')
for img in imgs[:5]:
    print(f'  {img}')

# Also check the page structure
content_blocks = re.findall(r'<a href="(https?://www\.ooanime\.com/series/\d+/[^"]+)"[^>]*>\s*<img[^>]*src="([^"]+)"[^>]*alt="([^"]*)"', t)
print(f'\nContent blocks (link+img+alt): {len(content_blocks)}')
for link, img, alt in content_blocks[:10]:
    print(f'  {link}')
    print(f'    img: {img}')
    print(f'    title: {alt}')
