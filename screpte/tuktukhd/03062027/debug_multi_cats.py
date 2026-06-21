import requests, re
headers = {'User-Agent': 'Mozilla/5.0'}

# Check a few known pages from our database
test_urls = [
    'https://tuktukhd.com/%d9%81%d9%8a%d9%84%d9%85-erupcja-2026-%d9%85%d8%aa%d8%b1%d8%ac%d9%85/',  # foreign
    'https://tuktukhd.com/%d9%81%d9%8a%d9%84%d9%85-sathi-leelavathi-2026-%d9%85%d8%aa%d8%b1%d8%ac%d9%85/',  # Indian? 
    'https://tuktukhd.com/%d9%81%d9%8a%d9%84%d9%85-%d8%a7%d9%84%d9%86%d8%a7%d8%a6%d9%85-the-sleeper-2025-%d9%85%d8%aa%d8%b1%d8%ac%d9%85/',  # Turkish
]

for url in test_urls:
    print('URL:', url[:60] if len(url) > 60 else url)
    try:
        r = requests.get(url, timeout=15, headers=headers)
        html = r.content.decode('utf-8')
        
        # Find catssection
        cs = re.search(r'class="catssection"[^>]*>(.*?)</section>', html, re.DOTALL)
        if cs:
            cats = re.findall(r'<a[^>]*href="([^"]*category[^"]*)"[^>]*>([^<]+)</a>', cs.group(1))
            print('  cats in catssection:')
            for href, label in cats:
                print('    {} -> {}'.format(label, href))
        else:
            print('  catssection not found')
        
        # Check for Netflix
        is_netflix = 'film-netflix' in html or 'نتفليكس' in html or 'Netflix' in html
        print('  Netflix detected:', is_netflix)
        
    except Exception as e:
        print('  Error:', e)
    print()
