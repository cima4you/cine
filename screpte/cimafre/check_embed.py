import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
    'Referer': 'https://cimafre.site/',
}

s = requests.Session()
s.get('https://cimafre.site/', headers=headers, timeout=20)

r = s.get('https://cimafre.site/embed.php?vid=19997b01f', headers=headers, timeout=20)
r.encoding = 'utf-8'
print(f'Embed page: {r.status_code}, {len(r.text)} bytes')
print(r.text[:3000])
print('...')
print(r.text[-500:])
