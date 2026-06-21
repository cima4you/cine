import requests, re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
}
s = requests.Session()
s.get('https://cimafre.site/', headers=headers, timeout=20)

vids = ['19997b01f', '2eb07be03', 'f65d2661e', '5330ecebb', 'c661d1499']

for vid in vids:
    r = s.get(f'https://cimafre.site/embed.php?vid={vid}', headers=headers, timeout=15)
    r.encoding = 'utf-8'
    m = re.search(r'<iframe[^>]*src="([^"]+)"', r.text)
    src = m.group(1) if m else 'NO SOURCE'
    print(f'{vid}: {src}')
