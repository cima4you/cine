import requests, re, html

headers = {'User-Agent': 'Mozilla/5.0'}

for page in [1, 2, 13, 14, 15]:
    url = 'https://tuktukhd.com/category/anime-6/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d9%86%d9%85%d9%8a/'
    if page > 1:
        url = url.rstrip('/') + '/page/{}/'.format(page)
    
    r = requests.get(url, headers=headers, timeout=15)
    items = re.findall(
        r'<a[^>]*href="(https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+)"[^>]*>.*?<img[^>]*alt="([^"]+)"[^>]*>.*?</a>',
        r.text, re.DOTALL
    )
    alt_patterns = {}
    for href, alt in items:
        # Check pattern
        m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم(?:\s+اون\s+لاين)?', alt)
        key = 'MATCH' if m else 'NO_MATCH'
        if key not in alt_patterns:
            alt_patterns[key] = []
        if len(alt_patterns[key]) < 3:
            alt_patterns[key].append(alt[:80])
    
    print('Page {}: {} items'.format(page, len(items)))
    for k, v in alt_patterns.items():
        print('  {}:'.format(k))
        for a in v:
            print('    {}'.format(a))
    print()
