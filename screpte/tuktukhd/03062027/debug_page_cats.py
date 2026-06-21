import requests, re
headers = {'User-Agent': 'Mozilla/5.0'}

# Check a few specific movie pages
urls = [
    'https://tuktukhd.com/%d9%81%d9%8a%d9%84%d9%85-erupcja-2026-%d9%85%d8%aa%d8%b1%d8%ac%d9%85/',  # مهمل - likely foreign
    'https://tuktukhd.com/%d9%81%d9%8a%d9%84%d9%85-casa-grande-2026-%d9%85%d8%aa%d8%b1%d8%ac%d9%85/',  # Casa Grande - likely foreign
]

for url in urls:
    print('=== URL:', url[:60], '===') 
    r = requests.get(url, timeout=15, headers=headers)
    html = r.content.decode('utf-8')
    
    # Look for the right sidebar categories section
    # Find all category links
    cat_links = re.findall(r'<a[^>]*href="[^"]*category[^"]*"[^>]*>([^<]+)</a>', html)
    print('All category links in page:')
    for c in cat_links:
        print('  - {}'.format(c.strip()))
    
    # Look for specific page/category indicators
    # Find the URL slug path
    print()
    print('URL path:', url.split('tuktukhd.com')[1] if 'tuktukhd.com' in url else '')
    print()
    
    # Check what's inside the "details" section for category
    det_section = re.search(r'class="[^"]*genres[^"]*"[^>]*>(.*?)</ul>', html, re.DOTALL)
    if det_section:
        print('Found genres section')
    
    # Look for category-specific content blocks
    for pattern in ['class="[^"]*catssection[^"]*"', 'class="[^"]*categories[^"]*"', 'class="[^"]*tags[^"]*"', 'id="[^"]*category']:
        m = re.search(pattern, html)
        if m:
            print('Found:', m.group())
    
    print('\n---\n')
