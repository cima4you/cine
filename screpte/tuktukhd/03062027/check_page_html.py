import requests, re

headers = {'User-Agent': 'Mozilla/5.0'}
url = 'https://tuktukhd.com/category/anime-6/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d9%86%d9%85%d9%8a/page/2/'
r = requests.get(url, headers=headers, timeout=15)

# Find all poster-related HTML blocks
blocks = re.findall(r'<li[^>]*class="[^"]*TPost[^"]*"[^>]*>.*?</li>', r.text, re.DOTALL)
print('TPost blocks: {}'.format(len(blocks)))

for i, block in enumerate(blocks[:3]):
    print('\nBlock {}:'.format(i+1))
    # Find href and alt inside block
    a = re.search(r'href="([^"]+)"', block)
    img = re.search(r'<img[^>]*alt="([^"]+)"', block)
    if a: print('  href: {}'.format(a.group(1)[:70]))
    if img: print('  alt: {}'.format(img.group(1)[:70]))

# Also check for different HTML patterns
if not blocks:
    # Try TPostMv or other classes
    for cls in ['TPost', 'TPostMv', 'poster', 'movie', 'item', 'film']:
        bs = re.findall(r'<li[^>]*class="[^"]*{}[^"]*"[^>]*>.*?</li>'.format(cls), r.text, re.DOTALL)
        if bs:
            print('Found {} blocks with class {}'.format(len(bs), cls))
            break

# Check the ol/ul containing the movies
lists = re.findall(r'<(?:ul|ol)[^>]*class="[^"]*"[^>]*>(.*?)</(?:ul|ol)>', r.text, re.DOTALL)
print('\nLists found: {}'.format(len(lists)))
for i, lst in enumerate(lists):
    items = re.findall(r'<li', lst)
    print('  List {}: {} items'.format(i+1, len(items)))
