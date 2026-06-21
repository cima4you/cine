import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

r = requests.get('https://cimafre.site/js/melody.dev.js', headers=headers, timeout=20)
r.encoding = 'utf-8'
t = r.text
print(f'Full melody.dev.js ({len(t)} bytes):')
print(t)
