import requests, re
headers = {'User-Agent': 'Mozilla/5.0'}

url = 'https://tv8.egydead.live/sinners-2025-1080p-bluray/'
r = requests.get(url, timeout=15, headers=headers)
html = r.content.decode('utf-8')
print('Length:', len(html))

# Look for video/servers
for p in ['data-crypt', 'data-real-url', 'server--item', 'server-item', 'iframe']:
    matches = re.findall(p, html)
    print('  {}: {}'.format(p, len(matches)))

# Show a snippet around 'server'
idx = html.find('server')
if idx > 0:
    print('  Server context:', html[max(0,idx-50):idx+300])

# Show around تحميل
idx = html.find('تحميل')
if idx > 0:
    print('  Download context:', html[max(0,idx-50):idx+300])

# Check for og tags
for pat in ['og:image', 'og:description', 'property="og:']:
    m = re.search(r'<meta[^>]*{}[^>]*>'.format(re.escape(pat)), html)
    if m:
        print('  Found og:', m.group()[:120])

# Find player iframe/video sources
for pat in [r'<iframe[^>]*src="([^"]+)"', r'<video[^>]*src="([^"]+)"', r'<source[^>]*src="([^"]+)"']:
    for m in re.finditer(pat, html):
        print('  Source:', m.group(1)[:80])
        break

# Find any embedded URLs
for m in re.finditer(r'https?://[^\s"<>]+\.(?:m3u8|mp4)[^\s"<>]*', html):
    print('  Video URL:', m.group()[:80])
    break
