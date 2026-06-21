import requests, re, concurrent.futures, json, urllib.parse

headers = {'User-Agent': 'Mozilla/5.0'}

# Fetch all sitemap indexes to get individual sitemap URLs
r = requests.get('https://tuktukhd.com/sitemap.xml', timeout=15, headers=headers)
sitemap_urls = re.findall(r'<loc>([^<]+)</loc>', r.text)

# Filter only post-sitemap files
post_sitemaps = [s for s in sitemap_urls if 'post-sitemap' in s]
print('Total post sitemaps: {}'.format(len(post_sitemaps)))

# Process a few sitemaps to estimate film URL count
def check_sitemap(url):
    r = requests.get(url, timeout=15, headers=headers)
    all_urls = re.findall(r'<loc>([^<]+)</loc>', r.text)
    film_urls = [u for u in all_urls if '/%D9%81%D9%8A%D9%84%D9%85' in u]
    return (url, len(film_urls), len(all_urls))

# Check first 10 sitemaps
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
    results = list(ex.map(check_sitemap, post_sitemaps[:10]))

total_films = 0
total_all = 0
for url, films, total in sorted(results):
    print('{}: {} films / {} total'.format(url.split('/')[-1], films, total))
    total_films += films
    total_all += total

print('\nFirst 10 sitemaps: {} films out of {} total'.format(total_films, total_all))
