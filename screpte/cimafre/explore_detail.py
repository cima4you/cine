import requests, re, json

BASE = 'https://cimafre.site'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# First, get movie links from the listing page
r = requests.get(BASE + '/category.php?cat=arabic-moives&page=1&order=DESC', headers=HEADERS, timeout=20)
r.encoding = 'utf-8'
t = r.text

# Find all movie detail links
movies = re.findall(r'<a\s+href="(watch\.php\?vid=[^"]+)"[^>]*>\s*<img[^>]*src="([^"]+)"[^>]*alt="([^"]*)"', t)
print(f'Movies on page 1: {len(movies)}')
for link, poster, alt in movies[:3]:
    print(f'\n  Link: {link}')
    print(f'  Alt: {alt}')
    print(f'  Poster: {poster}')

# Visit the first movie detail page
if movies:
    vid_url = BASE + '/' + movies[0][0]
    print(f'\n\n=== Detail page: {vid_url} ===')
    r2 = requests.get(vid_url, headers=HEADERS, timeout=20)
    r2.encoding = 'utf-8'
    t2 = r2.text
    print(f'Status: {r2.status_code}, Length: {len(t2)}')

    # Extract data from detail page
    # Watch servers
    watch_servers = re.findall(r'<li[^>]*data-embed-id="(\d+)"[^>]*data-embed-url="([^"]+)"', t2)
    print(f'\nWatch servers: {len(watch_servers)}')
    for sid, url in watch_servers[:5]:
        names = re.findall(r'<strong>([^<]+)</strong>', t2[t2.find(f'data-embed-id="{sid}"'):])
        name = names[0] if names else '?'
        print(f'  {name}: {url[:70]}')

    # Download servers
    download_servers = re.findall(r'<li[^>]*data-download-id="(\d+)"[^>]*data-download-url="([^"]+)"', t2)
    print(f'\nDownload servers: {len(download_servers)}')
    for sid, url in download_servers[:3]:
        print(f'  {url[:70]}')

    # Description
    desc = re.search(r'<p>(.*?)</p>', t2, re.DOTALL)
    if desc:
        desc_text = re.sub(r'<[^>]+>', '', desc.group(1)).strip()
        print(f'\nDescription: {desc_text[:200]}')

    # Year from title
    title_match = re.search(r'<title>(.*?)</title>', t2)
    if title_match:
        print(f'\nTitle tag: {title_match.group(1)[:100]}')
