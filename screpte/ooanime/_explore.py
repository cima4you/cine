import requests, re, json

url = 'https://www.ooanime.com/cartoon'
r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
r.encoding = 'utf-8'
text = r.text

# Save page HTML to inspect
with open('page.html', 'w', encoding='utf-8') as f:
    f.write(text)

# Find all series links
series_links = re.findall(r'href="(/series/\d+/[^"]+)"', text)
print(f'Series links found: {len(series_links)}')
for sl in series_links[:10]:
    print(f'  {sl}')

# Find episode links on page
episode_links = re.findall(r'href="(/episode/\d+/[^"]+)"', text)
print(f'\nEpisode links found: {len(episode_links)}')
for el in episode_links[:5]:
    print(f'  {el}')

# Find video sources
video_sources = re.findall(r'<source[^>]*src="([^"]+)"', text)
print(f'\nVideo sources on page: {len(video_sources)}')
for vs in video_sources[:5]:
    print(f'  {vs}')

# Check pagination
pagination = re.findall(r'href="(/cartoon\?page=\d+)"', text)
print(f'\nPagination links: {len(pagination)}')
for p in pagination[:10]:
    print(f'  {p}')
