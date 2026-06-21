import requests, re

headers = {'User-Agent': 'Mozilla/5.0'}
CATEGORY = 'https://tuktukhd.com/category/anime-6/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d9%86%d9%85%d9%8a'

# Test the MALFORMED URL (missing / before page/)
bad_url = CATEGORY + 'page/2/'
r_bad = requests.get(bad_url, headers=headers, timeout=15, allow_redirects=True)
print('BAD URL (no slash): {}'.format(bad_url[:80]))
print('  Status: {}, final_url: {}'.format(r_bad.status_code, r_bad.url[:60]))
items_bad = re.findall(
    r'<a[^>]*href="(https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+)"[^>]*>.*?<img[^>]*alt="([^"]+)"[^>]*>.*?</a>',
    r_bad.text, re.DOTALL
)
print('  Items found: {}'.format(len(items_bad)))

print()

# Test the CORRECT URL
good_url = CATEGORY + '/page/2/'
r_good = requests.get(good_url, headers=headers, timeout=15, allow_redirects=True)
print('GOOD URL (with slash): {}'.format(good_url[:80]))
print('  Status: {}, final_url: {}'.format(r_good.status_code, r_good.url[:60]))
items_good = re.findall(
    r'<a[^>]*href="(https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+)"[^>]*>.*?<img[^>]*alt="([^"]+)"[^>]*>.*?</a>',
    r_good.text, re.DOTALL
)
print('  Items found: {}'.format(len(items_good)))
