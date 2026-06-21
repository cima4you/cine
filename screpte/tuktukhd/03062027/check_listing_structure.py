import requests, re, json
headers = {'User-Agent': 'Mozilla/5.0'}
# Check listing page
r = requests.get('https://tuktukhd.com/category/movies-2/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d8%ac%d9%86%d8%a8%d9%8a/', timeout=15, headers=headers)

# Find Block--Item elements and extract info
blocks = re.findall(r'<div class="Block--Item">(.*?)</div>\s*</div>', r.text, re.DOTALL)
print('Found {} Block--Item blocks'.format(len(blocks)))

if blocks:
    # Check first block
    b = blocks[0]
    # aria-label on img
    aria = re.search(r'alt="([^"]*)"', b)
    if aria:
        print('alt:', aria.group(1))
    # Look for any text content
    text_content = re.sub(r'<[^>]+>', ' ', b)
    text_content = re.sub(r'\s+', ' ', text_content).strip()
    print('Text:', text_content[:200])
    # Also check for title attribute
    title = re.search(r'title="([^"]*)"', b)
    if title:
        print('title:', title.group(1))
    
# Also try the actual image src
imgs = re.findall(r'<img[^>]*src="([^"]+)"[^>]*>', r.text)
for img in imgs[:3]:
    print('Image src:', img)

# Try finding movie names directly
movie_names = re.findall(r'alt="(فيلم [^"]*)"', r.text)
print('\nMovie names from alt tags:')
for m in movie_names[:5]:
    print('  {}'.format(m))
