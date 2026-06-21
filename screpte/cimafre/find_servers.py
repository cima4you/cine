import requests, re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
}
s = requests.Session()
s.get('https://cimafre.site/', headers=headers, timeout=20)

vid = '19997b01f'
r = s.get(f'https://cimafre.site/watch.php?vid={vid}', headers=headers, timeout=20)
r.encoding = 'utf-8'
t = r.text

# Find ALL inline scripts between <script> and </script>
scripts = re.findall(r'<script[^>]*>(.*?)</script>', t, re.DOTALL)
print(f'Total scripts: {len(scripts)}')

# Look for any variable that contains server or source data
for i, s in enumerate(scripts):
    s = s.strip()
    if not s:
        continue
    # Skip libraries, CSS, comments
    if s.startswith('//') or s.startswith('$(function') or s.startswith('$(document'):
        continue
    # Check for relevant keywords
    for kw in ['WatchList', 'DownloadList', 'data-embed', 'server_name', 'sources', 'servers']:
        if kw.lower() in s.lower():
            print(f'\nScript {i} ({len(s)} chars) — contains "{kw}":')
            # Show lines with the keyword
            for line in s.split('\n'):
                ls = line.strip()
                if kw.lower() in ls.lower():
                    print(f'  {ls[:200]}')

# Also check for any hidden divs or JSON-like data
print('\n=== Hidden data in HTML ===')
for kw in ['source', 'server', 'watch_url', 'download_url']:
    matches = re.findall(rf'["\']{{0}}[\w_]{{0,10}}{kw}[\w_]{{0,10}}["\']{{0}}\s*:\s*["\'][^"\']+["\']', t, re.IGNORECASE)
    if matches:
        print(f'{kw}: {len(matches)} matches')
        for m in matches[:5]:
            print(f'  {m[:150]}')
