import requests, re, json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://cimafre.site/',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
}

s = requests.Session()
s.get('https://cimafre.site/', headers=headers, timeout=20)

# Fetch the albaplayer page
url = 'https://hd.cimaf.xyz/albaplayer/el-kalam-ala-eh/'
r = s.get(url, headers=headers, timeout=20)
r.encoding = 'utf-8'
t = r.text
print(f'Albaplayer page: {r.status_code}, {len(t)} bytes')

# Check for albaplayer.js
m = re.search(r'src="([^"]*albaplayer\.js[^"]*)"', t)
if m:
    js_url = m.group(1)
    if js_url.startswith('//'):
        js_url = 'https:' + js_url
    elif js_url.startswith('/'):
        js_url = 'https://hd.cimaf.xyz' + js_url
    print(f'AlbaPlayer JS: {js_url}')
    r2 = s.get(js_url, headers=headers, timeout=20)
    r2.encoding = 'utf-8'
    js = r2.text
    print(f'  {len(js)} bytes')
    # Look for source URLs or server data
    if 'source' in js.lower():
        for line in js.split('\n'):
            if 'source' in line.lower() and len(line.strip()) > 10:
                print(f'  {line.strip()[:200]}')
    if 'http' in js:
        urls = re.findall(r'https?://[^"\']+\.(?:m3u8|mp4)[^"\'\\]*', js)
        if urls:
            print(f'  Direct video URLs:')
            for u in urls[:5]:
                print(f'    {u}')

# Also check for a config/data JSON
data_patterns = re.findall(r'(\w+)\s*:\s*"([^"]+)"', t)
sources = [x for x in data_patterns if any(k in x[0].lower() for k in ['source', 'file', 'url', 'video', 'stream'])]
if sources:
    print('\nSource-like data:')
    for k, v in sources:
        print(f'  {k}: {v}')
