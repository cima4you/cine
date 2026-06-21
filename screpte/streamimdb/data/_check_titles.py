import requests, re

r = requests.get('https://streamimdb.ru/movies?vaplayer_path=movies&page=1',
  headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
r.encoding = 'utf-8'

# Find img alt and h3 title for first few cards
cards = re.findall(r'<div class="cb-card".*?</div>', r.text, re.DOTALL)
print(f'Found {len(cards)} cards on page 1')
for i, card in enumerate(cards[:5]):
    img = re.search(r'<img[^>]*alt="([^"]*)"', card)
    h3 = re.search(r'<h3 class="cb-card-title">(.*?)</h3>', card, re.DOTALL)
    a = re.search(r'href="/movie/([^"]+)"', card)
    slug = a.group(1) if a else '?'
    # Also look for any other title-like text
    meta = re.search(r'<p class="cb-card-meta">(.*?)</p>', card, re.DOTALL)
    print(f'  [{i}] slug={slug}')
    print(f'       img_alt={repr(img.group(1)) if img else "NONE"}')
    print(f'       h3_title={repr(h3.group(1).strip()) if h3 else "NONE"}')
    print(f'       meta={repr(meta.group(1).strip()) if meta else "NONE"}')
