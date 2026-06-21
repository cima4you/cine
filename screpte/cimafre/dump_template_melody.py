import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
}

r = requests.get('https://cimafre.site/templates/echo/js/melody.dev.js', headers=headers, timeout=20)
r.encoding = 'utf-8'
t = r.text
print(f'Template melody.dev.js ({len(t)} bytes):')
print(t)
