import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://cimafre.site/',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
}

s = requests.Session()
s.get('https://cimafre.site/', headers=headers, timeout=20)

# Check the player page
url = 'https://hd.cimaf.xyz/albaplayer/el-kalam-ala-eh/'
r = s.get(url, headers=headers, timeout=20)
r.encoding = 'utf-8'
print(f'Player page: {r.status_code}, {len(r.text)} bytes')
print(r.text[:2000])
