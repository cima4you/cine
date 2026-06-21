import requests, re
headers = {'User-Agent': 'Mozilla/5.0'}
BASE = 'https://tuktukhd.com/category/movies-2/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d8%ac%d9%86%d8%a8%d9%8a'

r = requests.get(BASE, timeout=15, headers=headers, allow_redirects=True)
print('Status:', r.status_code)
print('URL:', r.url)
print()

# Debug: Find all alt attributes
alts = re.findall(r'alt="([^"]*)"', r.text)
print('All alt attributes:')
for a in alts[:20]:
    print('  "{}"'.format(a))

# Debug: Find all href with فيلم
hrefs = re.findall(r'href="([^"]*فيلم[^"]*)"', r.text)
print('\nHrefs with فيلم:')
for h in hrefs[:10]:
    print('  {}'.format(h))

# Check for the actual listing structure
if 'Block--Item' in r.text:
    print('\n"Block--Item" found in page')
    # Find blocks
    blocks = re.findall(r'<div class="Block--Item">(.*?)</div>', r.text, re.DOTALL)
    print('Blocks found:', len(blocks))
    if blocks:
        print('First block:', blocks[0][:300])
else:
    print('\n"Block--Item" NOT found')

# Check what div classes are used
div_classes = re.findall(r'<div class="([^"]*)"', r.text)
print('\nUnique div classes:')
for c in sorted(set(div_classes))[:30]:
    print('  {}'.format(c))
