import requests, re, time

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ar,en-US;q=0.9,en;q=0.8',
}

s = requests.Session()
r = s.get('https://cimafre.site/', headers=headers, timeout=20)

url = 'https://cimafre.site/category.php?cat=arabic-moives&page=1&order=DESC'
r = s.get(url, headers=headers, timeout=20)
r.encoding = 'utf-8'
print(f'Status: {r.status_code}, size: {len(r.text)}')

# Find all links with watch.php
import re
links = re.findall(r'<a[^>]*href="([^"]*watch\.php\?vid=[a-f0-9]+)[^"]*"[^>]*>(.*?)</a>', r.text, re.DOTALL)
print(f'Links with watch.php: {len(links)}')
for href, title in links[:5]:
    title_clean = re.sub(r'<[^>]+>', '', title).strip()
    vid = re.search(r'vid=([a-f0-9]+)', href).group(1)
    print(f'  {vid}: {title_clean[:80]}')

# Check for specific selectors
from bs4 import BeautifulSoup
soup = BeautifulSoup(r.text, 'html.parser')
# Check common selectors
for sel in ['.pm-video-thumb', 'article', '.item', '.video', '.col-md-3', '.col-xs-6', '.thumb', 'figure', '.poster']:
    els = soup.select(sel)
    if els:
        print(f'Selector "{sel}": {len(els)} elements')
        if els[0]:
            classes = els[0].get('class', [])
            print(f'  First element classes: {classes}')
            print(f'  First element HTML: {str(els[0])[:200]}')
