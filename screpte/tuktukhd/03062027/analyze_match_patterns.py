import requests, re, html

headers = {'User-Agent': 'Mozilla/5.0'}

for page in [1, 2, 3, 4, 5, 13, 14]:
    url = 'https://tuktukhd.com/category/anime-6/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d9%86%d9%85%d9%8a/'
    if page > 1:
        url = url.rstrip('/') + '/page/{}/'.format(page)
    
    r = requests.get(url, headers=headers, timeout=15)
    items = re.findall(
        r'<a[^>]*href="(https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+)"[^>]*>.*?<img[^>]*alt="([^"]+)"[^>]*>.*?</a>',
        r.text, re.DOTALL
    )
    
    match_count = 0
    no_match_patterns = {}
    for href, alt in items:
        alt_stripped = alt.strip()
        m = re.match(r'فيلم\s+(.+?)\s+(\d{4})\s+مترجم(?:\s+اون\s+لاين)?', alt_stripped)
        if m:
            match_count += 1
        else:
            # Categorize why it doesn't match
            if 'مدبلج' in alt_stripped:
                pattern = 'has مدبلج'
            elif re.match(r'فيلم\s+\d{4}\s+', alt_stripped):
                pattern = 'year-first'
            elif not re.match(r'فيلم', alt_stripped):
                pattern = 'no فيلم prefix'
            else:
                pattern = 'other: ' + alt_stripped[:60]
            if pattern not in no_match_patterns:
                no_match_patterns[pattern] = 0
            no_match_patterns[pattern] += 1
    
    print('Page {}: {} items, {} matched'.format(page, len(items), match_count))
    if no_match_patterns:
        for pattern, count in sorted(no_match_patterns.items()):
            print('  Non-match ({}): {}'.format(count, pattern[:80]))
