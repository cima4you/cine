import requests, re, json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://cimafre.site/',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
}

s = requests.Session()
s.get('https://cimafre.site/', timeout=20)

url = 'https://hd.cimaf.xyz/albaplayer/el-kalam-ala-eh/'
r = s.get(url, headers=headers, timeout=20)
r.encoding = 'utf-8'
t = r.text

# Extract all scripts
scripts = re.findall(r'<script[^>]*>(.*?)</script>', t, re.DOTALL)
print(f'Scripts: {len(scripts)}')
for i, sc in enumerate(scripts):
    sc = sc.strip()
    if not sc:
        continue
    print(f'\nScript {i} ({len(sc)} chars):')
    print(sc[:500])
    print('---')

# Extract all data-* attributes
print('\n\nData attributes:')
data_attrs = re.findall(r'data-[a-zA-Z-]+="[^"]*"', t)
for da in data_attrs:
    print(f'  {da[:200]}')

# Extract all JSON-like objects
print('\n\nJSON-like objects:')
for m in re.finditer(r'\{[^{}]*"[^"]+"\s*:[^}]+}', t):
    obj_str = m.group(0)
    if 'http' in obj_str or 'source' in obj_str.lower():
        print(f'  {obj_str[:300]}')
