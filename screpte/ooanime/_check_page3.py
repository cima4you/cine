import re, json

with open('page.html', 'r', encoding='utf-8') as f:
    t = f.read()

# Find all tcb-product-item content divs
items = re.findall(r'<div class="rgt tcb-product-item content">(.*?)</div>\s*</div>\s*</div>', t, re.DOTALL)
print(f'Found {len(items)} content items')

for i, item in enumerate(items[:3]):
    # Extract all links
    links = re.findall(r'href="([^"]+)"', item)
    imgs = re.findall(r'<img[^>]*src="([^"]+)"[^>]*>', item)
    titles = re.findall(r'alt="([^"]*)"', item)
    print(f'\nItem {i}:')
    print(f'  Links: {links[:5]}')
    print(f'  Images: {imgs[:3]}')
    print(f'  Titles: {titles[:3]}')
    print(f'  Raw length: {len(item)}')
