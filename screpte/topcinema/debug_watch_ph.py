import requests, re

url = 'https://web.topcinemaa.com/%D9%81%D9%8A%D9%84%D9%85-personhood-2025-%D9%85%D8%AA%D8%B1%D8%AC%D9%85-%D8%A7%D9%88%D9%86-%D9%84%D8%A7%D9%8A%D9%86/watch/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
}
r = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
print('Status:', r.status_code)
print('Final URL:', r.url)
print('Length:', len(r.text))

with open('D:\\Users\\DT01\\Desktop\\rachid-site\\scripts\\topcinema\\debug_watch_personhood.html', 'w', encoding='utf-8') as f:
    f.write(r.text)
