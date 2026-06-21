import requests, re, json

url = 'https://www.ooanime.com/series/227/كوكي_العجيب'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
r.encoding = 'utf-8'
t = r.text

print(f'Page length: {len(t)}')

# Check title
m = re.search(r'<title>(.*?)</title>', t)
title = m.group(1).strip() if m else 'NONE'
print(f'Title: {title.encode("ascii", "replace").decode()}')

# Find all episode links with various patterns
ep1 = re.findall(r'href="(https?://www\.ooanime\.com/episode/\d+/[^"]+)"', t)
print(f'\nFull episode links: {len(ep1)}')

ep2 = re.findall(r'href="(/episode/\d+/[^"]+)"', t)
print(f'Relative episode links: {len(ep2)}')
for e in ep2[:5]: print(f'  {e}')

# Find season-col divs
seasons = re.findall(r'<div class="rgt season-col"[^>]*>(.*?)</div>\s*</div>', t, re.DOTALL)
print(f'\nSeason col divs: {len(seasons)}')
for s in seasons[:3]:
    links = re.findall(r'href="([^"]+)"', s)
    imgs = re.findall(r'src="([^"]+)"', s)
    print(f'  Links: {links}')
    print(f'  Images: {imgs}')

# Check for HomePage or episode container
homepage = re.findall(r'<div id="HomePage"[^>]*>(.*?)</div>', t, re.DOTALL)
print(f'\nHomePage divs: {len(homepage)}')
if homepage:
    ep3 = re.findall(r'href="(/episode/\d+/[^"]+)"', homepage[0])
    print(f'Episodes in HomePage: {len(ep3)}')
    for e in ep3[:5]: print(f'  {e}')

# Check for video source in page  
videos = re.findall(r'<source[^>]*src="([^"]+)"', t)
print(f'\nVideo sources: {len(videos)}')
for v in videos[:5]: print(f'  {v}')

iframes = re.findall(r'<iframe[^>]*src="([^"]+)"', t)
print(f'\nIframes: {len(iframes)}')
for f in iframes[:5]: print(f'  {f}')

# Save page for inspection
with open('series_page.html', 'w', encoding='utf-8') as f:
    f.write(t)
