from curl_cffi import requests as curl_requests
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
}

# Test homepage
r = curl_requests.get('https://tv8.egydead.live/', impersonate='chrome124', headers=headers)
print('Homepage: status={}, len={}, blocked={}'.format(
    r.status_code, len(r.text), 'Just a moment' in r.text or 'challenge' in r.text.lower()[:200]))

if 'Just a moment' not in r.text and r.status_code == 200:
    items = re.findall(r'<li class="movieItem">(.*?)</li>', r.text, re.DOTALL)
    print('Items on homepage:', len(items))
    if items:
        print('First item:', items[0][:300])

# Test category
r2 = curl_requests.get('https://tv8.egydead.live/category/english-movies/', impersonate='chrome124', headers=headers)
print('Category: status={}, len={}, blocked={}'.format(
    r2.status_code, len(r2.text), 'Just a moment' in r2.text or 'challenge' in r2.text.lower()[:200]))

if 'Just a moment' not in r2.text and r2.status_code == 200:
    items = re.findall(r'<li class="movieItem">(.*?)</li>', r2.text, re.DOTALL)
    print('Items on category:', len(items))

# Test detail page
r3 = curl_requests.get('https://tv8.egydead.live/sinners-2025-1080p-bluray/', impersonate='chrome124', headers=headers)
print('Detail: status={}, len={}, blocked={}'.format(
    r3.status_code, len(r3.text), 'Just a moment' in r3.text or 'challenge' in r3.text.lower()[:200]))
if 'Just a moment' not in r3.text:
    print('Detail HTML (first 500):')
    print(r3.text[:500])
