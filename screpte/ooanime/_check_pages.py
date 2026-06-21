import requests, re, json

def get_page(url):
    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    r.encoding = 'utf-8'
    return r.text

# Check if there's pagination
t = get_page('https://www.ooanime.com/cartoon')
pages = re.findall(r'\?page=(\d+)', t)
print(f'Pages found: {pages[:20]}')

# Check for "next" or pagination links
next_links = re.findall(r'class="[^"]*page-link[^"]*"[^>]*href="([^"]*)"[^>]*>التالي', t)
print(f'Next page links: {next_links}')
prev_links = re.findall(r'class="[^"]*page-link[^"]*"[^>]*href="([^"]*)"[^>]*>السابق', t)
print(f'Prev page links: {prev_links}')

# All pagination links
pag_links = re.findall(r'href="(/cartoon\?page=\d+)"', t)
print(f'Pagination links: {pag_links[:20]}')

# Now check a series page
t2 = get_page('https://www.ooanime.com/series/227/كوكي_العجيب')
# Find episodes
episodes = re.findall(r'href="(https?://www\.ooanime\.com/episode/\d+/[^"]+)"', t2)
print(f'\nSeries page episodes: {len(episodes)}')
for e in episodes[:5]: print(f'  {e}')

# Find video source on episode page
t3 = get_page('https://www.ooanime.com/episode/10178/الموسم_الاول_الحلقة_1')
videos = re.findall(r'<source[^>]*src="([^"]+)"', t3)
print(f'\nEpisode page video sources: {len(videos)}')
for v in videos[:5]: print(f'  {v}')

# Find the video tag
video_tag = re.findall(r'<video[^>]*>(.*?)</video>', t3, re.DOTALL)
print(f'Video tags: {len(video_tag)}')
for v in video_tag[:2]: print(f'  {v[:200]}')

# Also check for any embed/iframe
iframes = re.findall(r'<iframe[^>]*src="([^"]+)"', t3)
print(f'Iframes: {len(iframes)}')
for f in iframes[:5]: print(f'  {f}')
