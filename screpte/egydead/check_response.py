import requests
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'}

url = 'https://tv8.egydead.live/sinners-2025-1080p-bluray/'
r = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
html = r.content.decode('utf-8', errors='replace')
print('Status:', r.status_code)
print('Length:', len(html))
print('Final URL:', r.url)
print()
print(html[:2000])
