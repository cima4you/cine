import cloudscraper
scraper = cloudscraper.create_scraper()
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# Test homepage
url = 'https://tv8.egydead.live/'
r = scraper.get(url, timeout=20, headers=headers)
print('Homepage status:', r.status_code, 'Length:', len(r.text), 'Cloudflare:', 'Just a moment' in r.text)

# Test category page  
url2 = 'https://tv8.egydead.live/category/english-movies/'
r2 = scraper.get(url2, timeout=20, headers=headers)
print('Category status:', r2.status_code, 'Length:', len(r2.text), 'Cloudflare:', 'Just a moment' in r2.text)

# Test with different browser
for ua in [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
]:
    s2 = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    r3 = s2.get(url2, timeout=20, headers={'User-Agent': ua})
    print('  UA={}: status={}, len={}, blocked={}'.format(ua[:30], r3.status_code, len(r3.text), 'Just a moment' in r3.text))
