import requests, re

headers = {'User-Agent': 'Mozilla/5.0'}

# Check category for known anime titles
test_urls = [
    'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-meitantei-conan-movie-28-sekigan-no-flashback-2025-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/',
    'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-zootopia-2-2025-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/',
    'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-chainsaw-man-movie-reze-hen-2025-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/',
    'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-animal-farm-2026-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/',
    'https://tuktukhd.com/%D9%81%D9%8A%D9%84%D9%85-fate-stay-night-movie-heavens-feel-iii-spring-song-2020-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/',
]

for url in test_urls:
    try:
        r = requests.get(url, headers=headers, timeout=15)
        # Find the actual category
        m = re.search(r'التصنيفات\s*</span>\s*<a[^>]*>([^<]+)</a>', r.text)
        cat = m.group(1).strip() if m else 'NOT FOUND'
        
        # Also get title from og:title
        t = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', r.text)
        title = t.group(1)[:60] if t else 'UNKNOWN'
        
        print('{}  ->  {}'.format(title.ljust(60), cat))
    except Exception as e:
        print('Error: {}'.format(e))
