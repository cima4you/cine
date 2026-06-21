import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = 'https://yam.ahwaktv.net'
url = BASE + '/category.php?cat=moslslat-ramadan-2024'
r = requests.get(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}, verify=False, timeout=30)

# Find pagination section
# Look for common pagination patterns
patterns = [
    r'page=(\d+)',
    r'pagination[^>]*>(.*?)</(?:ul|div|nav)',
    r'page_id=(\d+)',
    r'paged=(\d+)',
    r'/\?page=(\d+)',
    r'\?page=(\d+)',
    r'pagination',
    r'next',
    r'التالي',
    r'السابق',
    r'\d+\s*من\s*\d+',
]

print('=== Searching for pagination patterns ===')
for pat in patterns:
    matches = re.findall(pat, r.text, re.IGNORECASE | re.DOTALL)
    if matches:
        print('Pattern "%s": %s' % (pat, matches[:10]))

# Extract part of HTML around "page" or numbers near bottom
# Find the last 2000 chars
print('\n=== Last 2000 chars of HTML ===')
print(r.text[-2000:])

# Also look for common pagination classes
for cls in ['pagination', 'page-nav', 'page_nav', 'page-numbers', 'pager', 'pages']:
    if cls in r.text.lower():
        idx = r.text.lower().find(cls)
        print('\nFound "%s" at %d:' % (cls, idx))
        print(r.text[max(0,idx-200):idx+500])
        break
