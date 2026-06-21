import requests, sys
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://tv8.egydead.live/wp-content/uploads/2024/06/%D9%81%D9%8A%D9%84%D9%85-%D8%A8%D8%A7%D9%83%D9%8A-%D9%87%D8%A7%D9%86%D9%85%D8%A7-%D8%B6%D8%AF-%D9%83%D9%8A%D9%86%D8%BA%D8%A7%D9%86-%D8%A7%D8%B4%D9%88%D8%B1%D8%A7-2024-%D9%85%D8%AF%D8%A8%D9%84%D8%AC.jpg'

# Test 1: No referrer
r1 = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=10)
print('Test 1 - No referrer: Status=%d, Length=%d, Content-Type=%s' % (r1.status_code, len(r1.content), r1.headers.get('Content-Type','')))

# Test 2: With egydead.live referrer
r2 = requests.get(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://egydead.live/'
}, timeout=10)
print('Test 2 - Referer egydead.live: Status=%d, Length=%d, Content-Type=%s' % (r2.status_code, len(r2.content), r2.headers.get('Content-Type','')))

# Test 3: With tv8.egydead.live referrer
r3 = requests.get(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://tv8.egydead.live/'
}, timeout=10)
print('Test 3 - Referer tv8.egydead.live: Status=%d, Length=%d, Content-Type=%s' % (r3.status_code, len(r3.content), r3.headers.get('Content-Type','')))

# Test 4: With origin header
r4 = requests.get(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Origin': 'https://egydead.live'
}, timeout=10)
print('Test 4 - Origin: Status=%d, Length=%d, Content-Type=%s' % (r4.status_code, len(r4.content), r4.headers.get('Content-Type','')))

# Test 5: With our own domain as referrer (to simulate the actual hotlink case)
r5 = requests.get(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://rachid-site.example.com/'
}, timeout=10)
print('Test 5 - Referer rachid-site: Status=%d, Length=%d, Content-Type=%s' % (r5.status_code, len(r5.content), r5.headers.get('Content-Type','')))
