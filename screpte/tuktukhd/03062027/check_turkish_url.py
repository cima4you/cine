import requests, re, json
r = requests.get('https://tuktukhd.com/category/%D8%AA%D8%B1%D9%83%D9%8A/page/1/', headers={'User-Agent':'Mozilla/5.0'}, timeout=15)
print('Status:', r.status_code)
print('Len:', len(r.text))
# Find movie links
hrefs = re.findall(r'https://tuktukhd\.com/%D9%81%D9%8A%D9%84%D9%85[^"]+', r.text)
print('Movie hrefs:', len(hrefs))
# Find alt texts
alts = re.findall(r'alt="([^"]+)"', r.text)
print('Alt texts:', len(alts))
# Show samples
for a, h in zip(alts[:5], hrefs[:5]):
    print(f'  {a[:60]} -> {h[:60]}')
