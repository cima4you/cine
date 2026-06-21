import requests, re

headers = {'User-Agent': 'Mozilla/5.0'}

# Test BOTH regex patterns on the same page 2
url = 'https://tuktukhd.com/category/anime-6/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d9%86%d9%85%d9%8a/page/2/'
r = requests.get(url, headers=headers, timeout=15)

# Pattern 1: any alt text
items1 = re.findall(
    r'<a[^>]*href="(https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+)"[^>]*>.*?<img[^>]*alt="([^"]+)"[^>]*>.*?</a>',
    r.text, re.DOTALL
)

# Pattern 2: alt starts with فيلم only  
items2 = re.findall(
    r'<a[^>]*href="(https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+)"[^>]*>.*?<img[^>]*alt="(\u0641\u064A\u0644\u0645[^"]+)"[^>]*>.*?</a>',
    r.text, re.DOTALL
)

print('Pattern 1 (any alt): {} items'.format(len(items1)))
print('Pattern 2 (فيلم alt): {} items'.format(len(items2)))

# Check alt texts that Pattern 2 is missing
if len(items1) != len(items2):
    p2_alts = set(a for _, a in items2)
    for h, a in items1:
        if a not in p2_alts:
            print('  Missing from Pattern 2: {}'.format(a[:70]))
